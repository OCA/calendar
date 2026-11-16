# Copyright (C) 2024 - ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import binascii
from datetime import date, datetime, time, timedelta, timezone

import pytz
import vobject
from lxml import html

from odoo import Command, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import html_sanitize, plaintext2html


class CalendarImportIcs(models.TransientModel):
    """Import iCalendar events into the selected partner's calendar."""

    _name = "calendar.import.ics"
    _description = "Calendar Import Ics"

    import_ics_file = fields.Binary(required=True)
    import_ics_filename = fields.Char()
    import_start_date = fields.Date("Start Import Date")
    import_end_date = fields.Date("End Import Date")
    partner_id = fields.Many2one("res.partner", string="Partner")
    do_remove_old_event = fields.Boolean(
        string="Remove old events?",
        help="If checked, the previously imported events "
        "that are not in this import will be deleted",
        default=True,
    )

    def button_import(self):
        self.ensure_one()
        if not (self.import_ics_filename or "").lower().endswith(".ics"):
            raise ValidationError(self.env._("Only .ics files are supported."))
        if not self.partner_id:
            self.partner_id = self.env.user.partner_id
        if not self.partner_id:
            raise ValidationError(
                self.env._("Select a calendar owner before importing.")
            )
        try:
            content = base64.b64decode(
                b"".join(self.import_ics_file.split()), validate=True
            ).decode("utf-8-sig")
            calendar = vobject.readOne(content)
            if calendar.name != "VCALENDAR":
                raise ValueError("Missing VCALENDAR component")
        except (
            binascii.Error,
            UnicodeError,
            ValueError,
            vobject.base.VObjectError,
        ) as exc:
            raise ValidationError(self.env._("Invalid ICS file: %s", exc)) from exc

        imported_uids = set()
        for component in calendar.contents.get("vevent", []):
            uid = self._import_event(component)
            if uid:
                imported_uids.add(uid)
        if self.do_remove_old_event:
            self._delete_non_imported_events(imported_uids)

    def _import_event(self, component):
        if {"recurrence-id", "exdate", "rdate", "exrule"} & component.contents.keys():
            raise ValidationError(
                self.env._("ICS recurrence exceptions are not supported.")
            )
        try:
            uid = component.uid.value.strip()
            name = component.summary.value
            start = component.dtstart.value
            end = component.dtend.value
        except AttributeError as exc:
            raise ValidationError(
                self.env._("Each ICS event needs a UID, title, start, and end.")
            ) from exc
        if (
            not uid
            or not name
            or not isinstance(start, (date, datetime))
            or type(start) is not type(end)
        ):
            raise ValidationError(
                self.env._("An ICS event has invalid required values.")
            )

        allday, start_utc, end_utc, last_date = self._event_dates(start, end)

        rule = component.rrule.value if "rrule" in component.contents else False
        if rule and (self.import_start_date or self.import_end_date):
            raise ValidationError(
                self.env._("Date filters are not supported for recurring ICS events.")
            )
        if rule:
            try:
                recurrence_values = self.env["calendar.recurrence"]._rrule_parse(
                    rule, start_utc
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValidationError(
                    self.env._("Invalid ICS recurrence rule.")
                ) from exc
        if self.import_start_date and start_utc.date() < self.import_start_date:
            return False
        if self.import_end_date and last_date > self.import_end_date:
            return False

        vals = {
            "name": name,
            "start": start_utc,
            "stop": end_utc,
            "allday": allday,
        }
        description = self._event_description(component)
        if description is not None:
            vals["description"] = description
        if rule:
            vals.update(
                {
                    "recurrency": True,
                    "rrule": rule,
                    "event_tz": (
                        "UTC"
                        if allday
                        else getattr(start.tzinfo, "zone", None) or "UTC"
                    ),
                }
            )
        events = self.env["calendar.event"].with_context(dont_notify=True)
        event = events.search([("event_identifier", "=", uid)], limit=1)
        if event:
            if event.recurrency and not rule:
                vals["recurrency"] = False
            if event.recurrency and rule:
                vals["recurrence_update"] = "all_events"
                vals.update(recurrence_values)
                vals.pop("rrule")
            if self.partner_id not in event.partner_ids:
                vals["partner_ids"] = [Command.link(self.partner_id.id)]
            event.write(vals)
        else:
            vals["event_identifier"] = uid
            vals["partner_ids"] = [Command.link(self.partner_id.id)]
            events.create(vals)
        return uid

    def _event_description(self, component):
        rich_description = component.contents.get("x-alt-desc", [])
        if (
            rich_description
            and rich_description[0].value.strip()
            and "text/html" in rich_description[0].params.get("FMTTYPE", [])
        ):
            rich_html = html.fragment_fromstring(
                html_sanitize(rich_description[0].value), create_parent=True
            )
            for image in rich_html.xpath(".//img[not(normalize-space(@src))]"):
                image.drop_tree()
            return html.tostring(rich_html, encoding="unicode")
        if "description" in component.contents:
            return plaintext2html(component.description.value)
        return None

    def _event_dates(self, start, end):
        allday = isinstance(start, date) and not isinstance(start, datetime)
        if allday:
            start_utc = datetime.combine(start, time.min)
            last_date = end - timedelta(days=1)
            end_utc = datetime.combine(last_date, time.min)
            valid = end > start
        else:
            start_utc = self._to_utc(start)
            end_utc = self._to_utc(end)
            last_date = end_utc.date()
            valid = end_utc > start_utc
        if not valid:
            raise ValidationError(self.env._("An ICS event must end after it starts."))
        return allday, start_utc, end_utc, last_date

    def _to_utc(self, value):
        if value.tzinfo is None:
            zone = pytz.timezone(self.env.user.tz or "UTC")
            try:
                value = zone.localize(value, is_dst=None)
            except (pytz.AmbiguousTimeError, pytz.NonExistentTimeError) as exc:
                raise ValidationError(
                    self.env._("The ICS event has an ambiguous local time.")
                ) from exc
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def _delete_non_imported_events(self, imported_uids):
        domain = [
            ("event_identifier", "!=", False),
            ("event_identifier", "not in", list(imported_uids)),
            ("partner_ids", "in", self.partner_id.id),
        ]
        if self.import_start_date:
            domain.append(("start", ">=", self.import_start_date))
        if self.import_end_date:
            domain.append(
                ("stop", "<=", datetime.combine(self.import_end_date, time.max))
            )
        for event in self.env["calendar.event"].search(domain):
            if len(event.with_context(active_test=False).partner_ids) == 1:
                event.unlink()
            else:
                event.write({"partner_ids": [Command.unlink(self.partner_id.id)]})
