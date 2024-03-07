# Copyright (C) 2024 - ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from datetime import datetime

import pytz
from dateutil import parser

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class CalendarImportIcs(models.TransientModel):
    """
    This wizard is used to import ics files to calendar
    """

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
        imported_events = []
        self.ensure_one()
        assert self.import_ics_file
        extension = self.import_ics_filename.split(".")[1]
        if extension != "ics":
            raise ValidationError(_("Only ics files are supported"))
        if self.env.user and not self.partner_id:
            self.partner_id = self.env.user.partner_id.id
        file_decoded = base64.b64decode(self.import_ics_file)
        file_str = file_decoded.decode("utf-8")
        lines = file_str.split("\n")
        ics_event = {}
        for line in lines:
            if line.startswith(("DTSTART", "DTEND")) and "TZID=" in line:
                line = self.convert_date_to_z(line)
            if line.startswith("BEGIN:VEVENT"):
                ics_event = {}
            elif line.startswith("END:VEVENT"):
                self._process_event(ics_event, imported_events)
            else:
                if ":" in line:
                    key, value = line.strip().split(":", 1)
                    ics_event[key] = value
        if self.do_remove_old_event:
            self._delete_non_imported_events(imported_events)

    def _process_event(self, ics_event, imported_events):
        if "DTSTART" in ics_event and "DTEND" in ics_event:
            event_start_date = self._parse_date(ics_event["DTSTART"])
            event_end_date = self._parse_date(ics_event["DTEND"])
            if (not self.import_start_date or not self.import_end_date) or (
                self.import_start_date <= event_start_date.date()
                and self.import_end_date >= event_end_date.date()
            ):
                imported_events.append(ics_event["UID"])
                event = self.env["calendar.event"].search(
                    [("event_identifier", "=", ics_event["UID"])]
                )
                if event:
                    self._update_event(
                        event, ics_event, event_start_date, event_end_date
                    )
                else:
                    self._create_event(ics_event, event_start_date, event_end_date)

    def _parse_date(self, date_str):
        return datetime.strptime(date_str, "%Y%m%dT%H%M%SZ")

    def _update_event(self, event, ics_event, event_start_date, event_end_date):
        vals = {}
        if event.start != event_start_date:
            vals["start"] = event_start_date
        if event.stop != event_end_date:
            vals["stop"] = event_end_date
        if event.name != ics_event["SUMMARY"]:
            vals["name"] = ics_event["SUMMARY"]
        if self.partner_id not in event.partner_ids:
            vals["partner_ids"] = [(4, self.partner_id.id, 0)]
        event.write(vals)

    def _create_event(self, ics_event, event_start_date, event_end_date):
        self.env["calendar.event"].create(
            {
                "start": event_start_date,
                "stop": event_end_date,
                "name": ics_event["SUMMARY"],
                "event_identifier": ics_event["UID"],
                "partner_ids": [(4, self.partner_id.id)],
            }
        )

    def _delete_non_imported_events(self, imported_events):
        domain = [
            ("event_identifier", "!=", False),
            ("event_identifier", "not in", imported_events),
            ("partner_ids", "in", self.partner_id.id),
        ]

        if self.import_start_date:
            domain.append(("start", ">=", self.import_start_date))

        if self.import_end_date:
            domain.append(("stop", "<=", self.import_end_date))

        non_imported_events = self.env["calendar.event"].search(domain)
        for non_imported_event in non_imported_events:
            non_imported_event.write({"partner_ids": [(3, self.partner_id.id)]})
        if not non_imported_events.partner_ids:
            non_imported_events.unlink()

    def convert_date_to_z(self, line):
        split_parts = line.split(":")
        event_phase = split_parts[0].split(";TZID=")[0]
        tz_id = split_parts[0].split(";TZID=")[1]
        date = split_parts[1]

        date_obj = parser.parse(date)
        tz = pytz.timezone(tz_id)

        utc_date = tz.localize(date_obj).astimezone(pytz.UTC)
        utc_date_string = utc_date.strftime(event_phase + ":%Y%m%dT%H%M%SZ")
        return utc_date_string
