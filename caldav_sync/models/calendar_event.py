import logging
import re
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

import caldav
import icalendar.cal
import markdown2 as md2
from caldav.lib.error import NotFoundError
from icalendar import Event, vCalAddress, vDate, vDatetime, vRecur, vText
from markdownify import markdownify as md
from pytz import timezone, utc

from odoo import api, fields, models

from odoo.addons.calendar.models.calendar_recurrence import MAX_RECURRENT_EVENT

_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from odoo.addons.base.models.res_partner import Partner
    from odoo.addons.base.models.res_users import Users as User
    from odoo.addons.calendar.models.calendar_event import Meeting as OdooCalendarEvent
else:
    User = models.Model
    Partner = models.Model
    OdooCalendarEvent = models.Model

WEEKDAY_MAP = {
    0: "MO",
    1: "TU",
    2: "WE",
    3: "TH",
    4: "FR",
    5: "SA",
    6: "SU",
}


def _parse_rrule_string(rrule_str: str) -> dict[str, Any]:
    """Parse a string representing an RRULE into a dictionary of its parts.

    Takes a string like "RRULE:FREQ=WEEKLY;UNTIL=20221231T000000Z;BYDAY=MO"
    and returns a dictionary with proper types for vRecur.
    """
    from icalendar import vFrequency, vWeekday

    def parse_value(key: str, value: str) -> Any:
        if key == "UNTIL":
            # Convert to datetime - vRecur expects raw datetime, not vDDDTypes
            if "T" in value:
                dt = datetime.strptime(value, "%Y%m%dT%H%M%S")
            else:
                dt = datetime.strptime(value, "%Y%m%d")
            return dt
        elif key in ("WKST", "BYDAY", "BYWEEKDAY"):
            # Convert to vWeekday
            return [vWeekday(day) for day in value.split(",")]
        elif key == "FREQ":
            # vFrequency will handle the conversion
            return vFrequency(value)
        elif key in (
            "COUNT",
            "INTERVAL",
            "BYSECOND",
            "BYMINUTE",
            "BYHOUR",
            "BYWEEKNO",
            "BYMONTHDAY",
            "BYYEARDAY",
            "BYMONTH",
            "BYSETPOS",
        ):
            # Convert to int or list of ints
            if "," in value:
                return [int(v) for v in value.split(",")]
            return int(value)
        return value

    if not rrule_str.startswith("RRULE:"):
        return {}

    params = rrule_str[6:]  # Remove 'RRULE:'
    result = {}
    for param in params.split(";"):
        if "=" in param:
            key, value = param.split("=", 1)
            key = key.upper()
            result[key] = parse_value(key, value)

    return result


def _extract_vcal_email(vcal_address):
    email_regex = re.compile(r"[a-z0-9.\-+_]+@[a-z0-9.\-+_]+\.[a-z]+")
    res = email_regex.search(str(vcal_address))
    return res.group(0).lower().strip() if res else ""


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    # CalDAV UID is either unique per event or the same for all events in a recurring
    # sequence. This field and caldav_recurrence_id are not calculated fields since
    # the recalculation timing is hard to control and we want to make sure we sync
    # some modifications before the UID changes with recurrence_id and other changes on
    # the record.
    caldav_uid = fields.Char(string="CalDAV UID", store=True)
    # Recurrence ID in iCalendar is the date or datetime the event would have
    # been at if it followed the sequence. It is set by calendar.recurrence
    # when applying a recurrence.
    caldav_recurrence_id = fields.Datetime(
        string="CalDAV Recurrence ID",
    )
    caldav_user_ids = fields.Many2many(
        comodel_name="res.users",
        compute="_compute_caldav_users",
    )
    is_base_event = fields.Boolean(compute="_compute_is_base_event")
    differs_from_base_event = fields.Boolean(compute="_compute_differs_from_base_event")

    ###################################
    #### Field Computation Methods ####
    ###################################

    def _recompute_caldav_ids(self):
        for event in self:
            if event.recurrence_id:
                event.caldav_uid = event.recurrence_id.caldav_uid
                time = event.recurrence_id.dtstart.time()
                date = event.start.date()
                event.caldav_recurrence_id = datetime(
                    date.year,
                    date.month,
                    date.day,
                    time.hour,
                    time.minute,
                    time.second,
                )
            else:
                if not self.env.context.get("caldav_keep_ids"):
                    event.caldav_uid = uuid.uuid4()
                event.caldav_recurrence_id = False

    @api.depends("name", "description", "partner_ids", "location", "videocall_location")
    def _compute_differs_from_base_event(self):
        base_events = self.filtered("is_base_event")
        non_base_events = self - base_events
        for event in base_events:
            event.differs_from_base_event = False
        fields_to_check = [
            "name",
            "description",
            "partner_ids",
            "location",
            "videocall_location",
        ]
        for event in non_base_events:
            base_event = event.recurrence_id.base_event_id
            event.differs_from_base_event = (
                any(
                    [
                        getattr(event, field) != getattr(base_event, field)
                        for field in fields_to_check
                    ]
                )
                or not event.follow_recurrence
            )

    @api.depends("recurrency", "recurrence_id", "recurrence_id.base_event_id")
    def _compute_is_base_event(self):
        for rec in self:
            rec.is_base_event = (
                not rec.recurrence_id or rec.recurrence_id.base_event_id == rec
            )

    @api.depends("user_id", "partner_ids", "partner_ids.user_id")
    def _compute_caldav_users(self):
        for rec in self:
            rec.caldav_user_ids = (rec.user_id | rec.partner_ids.user_ids).filtered(
                "is_caldav_enabled"
            )

    def _is_caldav_enabled(self):
        return self.user_id.is_caldav_enabled

    def _get_ical_recurrence_id(self) -> datetime:
        """Get the recurrence-id to use for identifying this event
        specifically in an iCalendar instance.

        :return: The timezone-aware datetime that uniquely identifies this
        event in the recurrence chain.
        """
        event_tz = timezone(self.event_tz) if self.event_tz else utc
        recurrence_id = utc.localize(self.caldav_recurrence_id).astimezone(event_tz)
        return recurrence_id

    #################################################################
    #### Local Change Methods - Sending Updates to CalDAV Server ####
    #################################################################

    @api.model_create_multi
    def create(self, vals_list):
        ctx = {"caldav_no_sync": True}
        events = super(CalendarEvent, self.with_context(**ctx)).create(vals_list)
        events.with_context(**ctx)._recompute_caldav_ids()
        if not self.env.context.get("caldav_no_sync"):
            events._to_sync()._sync_create_to_caldav()
        return events

    def _sync_create_to_caldav(self):
        for event in self:
            for user in event.caldav_user_ids:
                client = user._get_caldav_client()
                calendar = client.calendar(url=user.caldav_calendar_url)
                try:
                    caldav_events = event._create_in_icalendar(calendar)
                    for caldav_event in caldav_events:
                        caldav_uid = caldav_event.vobject_instance.vevent.uid.value  # pyright: ignore[reportAttributeAccessIssue]
                        event.with_context(caldav_no_sync=True).write(
                            {"caldav_uid": caldav_uid}
                        )
                except Exception as e:
                    _logger.error(
                        f"Failed to sync event to CalDAV server: {e}", exc_info=True
                    )

    def write(self, vals):
        # Capture state before write for future_events sync handling
        is_future_events_update = vals.get("recurrence_update") == "future_events"
        old_base_events = {}
        if is_future_events_update and not self.env.context.get("caldav_no_sync"):
            for event in self:
                if event.recurrence_id:
                    old_base_events[event.id] = event.recurrence_id.base_event_id

        res = super(CalendarEvent, self.with_context(caldav_no_sync=True)).write(vals)

        # Events sometimes get archived in Odoo in the process of updating recurrence
        # In that case, we will delete them from the CalDAV server before recreating
        if "active" in vals and not vals.get("active"):
            for event in self:
                event._sync_unlink_to_caldav()
            return res

        if self.env.context.get("caldav_no_sync"):
            return res

        # Handle future_events update sync - the split event becomes a new base event
        if is_future_events_update and old_base_events:
            for event in self._to_sync():
                # Remove old version from CalDAV (it was part of old recurrence)
                event._sync_unlink_to_caldav()
                # Sync the new base event (self after split)
                event._sync_write_to_caldav()
                # Sync the old base event (its recurrence was truncated)
                old_base = old_base_events.get(event.id)
                if old_base:
                    old_base._sync_write_to_caldav()
            return res

        # Normal sync for other write operations
        to_sync = self._to_sync()
        if to_sync:
            for rec in to_sync:
                rec._sync_write_to_caldav()
        return res

    def _sync_write_to_caldav(self):
        ical_event_data = self._create_event_data()
        for user in self.caldav_user_ids:
            client = user._get_caldav_client()
            calendar = client.calendar(url=user.caldav_calendar_url)

            base_event = self._get_caldav_base_event_by_uid(calendar, self.caldav_uid)
            if not base_event:
                _logger.debug(f"Failed to find base event for {self} on CalDAV server.")
                return
            if self.recurrence_id:
                tz = timezone(self.event_tz or self.env.user.tz or "UTC")
                start = utc.localize(self.start).astimezone(tz)
                # We have an event in the recurrence chain that differs from the base
                # We need to add an iCalendar VEVENT with recurrence-id or update it
                if self.is_base_event:
                    # We have a normal base event, so we just update it or create it
                    self._update_base_caldav_event(
                        calendar, base_event, ical_event_data
                    )
                elif (
                    self.differs_from_base_event
                    or start != self._get_ical_recurrence_id()
                ):
                    # Event differs from base, update or create its subcomponent
                    # identified by its recurrence-id
                    if not base_event:
                        _logger.debug(
                            f"Failed to find base event for {self} on CalDAV server."
                        )
                        return
                    index = self._get_subcomponent_index_for_recurrence(base_event)
                    if index:
                        ical_event = base_event.icalendar_instance.subcomponents[index]
                        self._update_ical_event_values(ical_event, ical_event_data)
                    else:
                        base_event.icalendar_instance.add_component(
                            Event(**ical_event_data)
                        )
                    base_event.save()
            else:
                self._update_base_caldav_event(calendar, base_event, ical_event_data)

    def _update_base_caldav_event(
        self,
        calendar: caldav.Calendar,
        event: caldav.Event,
        ical_event_data: dict,
    ):
        if event:
            self._update_ical_event_values(event.icalendar_component, ical_event_data)  # pyright: ignore[reportAttributeAccessIssue]
            event.save()
        else:
            calendar.add_event(**ical_event_data)

    def _update_ical_event_values(
        self, ical_event: icalendar.cal.Event, event_data: dict
    ):
        sequence = (ical_event.get("sequence") or 0) + 1
        event_data.update(sequence=sequence)
        for key, value in event_data.items():
            ical_event[key] = value

    def _get_caldav_base_event_by_uid(
        self, calendar: caldav.Calendar, uid: str
    ) -> caldav.Event | None:
        for event in calendar.events():
            component = event.icalendar_component  # pyright: ignore[reportAttributeAccessIssue]
            event_uid = self._extract_component_text(component, "uid")
            if event_uid == uid and not component.get("recurrence-id"):
                return event

    def unlink(self):
        if not self.env.context.get("caldav_no_sync"):
            for rec in self._to_sync():
                try:
                    rec._sync_unlink_to_caldav()
                except Exception as e:
                    _logger.error(f"Failed to delete event from CalDAV server: {e}")
        return super().unlink()

    def _get_subcomponent_index_for_recurrence(
        self, caldav_event: caldav.Event
    ) -> int | None:
        ical_instance = caldav_event.icalendar_instance
        for index, component in enumerate(ical_instance.subcomponents):
            if (
                component.get("name") == "VEVENT"
                and (rec_id := component.get("recurrence-id"))
                and rec_id.dt == self._get_ical_recurrence_id()
            ):
                return index

    def _sync_unlink_to_caldav(self):
        delete_all = self.env.context.get("caldav_delete_all", False)
        if self.caldav_uid:
            for user in self.caldav_user_ids:
                client = user._get_caldav_client()
                calendar = client.calendar(url=user.caldav_calendar_url)
                try:
                    caldav_event = calendar.event_by_uid(self.caldav_uid)
                    if not delete_all and self.recurrence_id and not self.is_base_event:
                        index = self._get_subcomponent_index_for_recurrence(
                            caldav_event
                        )
                        if index:
                            caldav_event.icalendar_instance.subcomponents.pop(index)
                        caldav_event.save()
                    else:
                        # Detached events can be base events with old caldav_uid.
                        # Make sure the start matches.
                        if delete_all or self._matches_caldav_start(caldav_event):
                            caldav_event.delete()
                except NotFoundError:
                    _logger.debug(
                        "Event %s not found on CalDAV server, nothing to sync",
                        self.caldav_uid,
                    )
                except Exception as e:
                    _logger.error(f"Failed to remove event from CalDAV server: {e}")

    def _matches_caldav_start(self, caldav_event: caldav.Event) -> bool:
        event_start = caldav_event.icalendar_component.get("dtstart").dt  # pyright: ignore[reportAttributeAccessIssue]
        tz = event_start.tzinfo
        if tz:
            self_start = utc.localize(self.start).astimezone(tz)
        else:
            # If event_start is naive, compare as naive UTC
            self_start = self.start
        # Compare without seconds/microseconds (iCalendar stores at minute precision)
        return self_start.replace(second=0, microsecond=0) == event_start.replace(
            second=0, microsecond=0
        )

    def _update_future_events(self, values, time_values, recurrence_values):
        """Override to ensure caldav IDs are refreshed for the new recurrence chain.

        The CalDAV sync is handled in write() which detects
        recurrence_update="future_events" and handles the sync there. This method
        just ensures the superclass behavior runs with the keep_caldav_ids=False
        context so new UIDs are generated.
        """
        if self.env.context.get("keep_caldav_ids") is not False:
            ctx = {"keep_caldav_ids": False}
            return (
                super()
                .with_context(**ctx)
                ._update_future_events(values, time_values, recurrence_values)
            )
        return super()._update_future_events(values, time_values, recurrence_values)

    def _break_recurrence(self, future=True):
        recurrence = self.recurrence_id
        detached_events = super()._break_recurrence(future) | self
        # detached_events are already removed from the CalDAV server in
        # calendar.recurrence._detach_events. We now need to reinitialize them.
        for event in detached_events:
            event._sync_write_to_caldav()
        if future:
            # When future=True, the base event needs to re-sync its recurrence values
            recurrence.base_event_id._sync_write_to_caldav()
        return detached_events - self

    def _rewrite_recurrence(self, values, time_values, recurrence_values):
        """
        When _rewrite_recurrence is called, it archives all the events in the
        recurrence but only after messing with the recurrence_id. This breaks our check
        on is_base_event, so we preemptively sync the deletion here.

        Because this method is usually called with caldav_no_sync=True in the context
        to avoid looping, we manually call _sync_write_to_caldav once the operation is
        completed.
        """
        for event in self.recurrence_id.calendar_event_ids:
            event.with_context(caldav_delete_all=True)._sync_unlink_to_caldav()
        res = super()._rewrite_recurrence(values, time_values, recurrence_values)
        for event in self.recurrence_id.calendar_event_ids:
            event._recompute_caldav_ids()
        self._sync_write_to_caldav()
        return res

    def _to_sync(self):
        """Determine which records in self we need to synchronize with the
        CalDAV server. In essence, we only synchronize base events and those
        differing from the base event in a recurring chain."""
        return self.filtered(
            lambda event: event.id
            and event._is_caldav_enabled()
            and (event.is_base_event or event.differs_from_base_event)
        )

    def _create_in_icalendar(self, calendar: caldav.Calendar) -> list[caldav.Event]:
        """Create an event matching self in the provided calendar.

        :param calendar: The calendar in which to create the event.
        :return: The list of created events, usually one.
        """
        ical_event_data = self._create_event_data()
        caldav_event = calendar.save_event(**ical_event_data)
        if self.recurrence_id and self.is_base_event and not self.follow_recurrence:
            ical_event_data = self._create_event_data()
            second_caldav_event = calendar.save_event(**ical_event_data)
            return [caldav_event, second_caldav_event]
        return [caldav_event]

    def _create_event_data(self) -> dict:
        """Create a dictionary of iCalendar compatible event data."""
        event_data = {}
        self._add_event_dates(event_data)
        self._add_event_header_info(event_data)
        self._add_event_attendees(event_data)
        if self.is_base_event and self.recurrence_id:
            self._add_event_recurrence(event_data)
        elif self.recurrence_id:
            self._add_event_recurrence_id(event_data)
        return event_data

    def _add_event_header_info(self, event_data: dict) -> None:
        """Add event header info to a dict containing event data.

        IMPORTANT: the VEVENT sequence is set to 0. It should be changed if this method
        is used to update an existing event!

        :param event_data: The dictionary of event data to be updated with header info.
        """
        event_data["uid"] = vText(self.caldav_uid)
        if self.name:
            event_data["summary"] = vText(self.name)
        # TODO: Consider using X-ALT-DESC to stick HTML into the iCal event desc.
        if self.description and self._html_to_text(self.description):
            event_data["description"] = vText(self._html_to_text(self.description))
        if self.location:
            event_data["location"] = vText(self.location)
        if self.videocall_location:
            event_data["conference"] = self.videocall_location
        event_data["sequence"] = 0

    def _add_event_dates(self, event_data: dict) -> None:
        """Add pertinent dates to event data, based on self.

        Determine timezone: prefer event_tz, then user tz, finally UTC.
        Note: All datetimes in Odoo are stored in UTC, so defaulting to UTC
        is correct. UTC times are sent in from the appointments app when
        installed, without timezone information. This was breaking the sync
        process due to a call to upper() on boolean value False.
        """
        tz = self.event_tz or self.env.user.tz or "UTC"
        event_tz = timezone(tz)
        event_data["last-modified"] = vDatetime(
            utc.localize(self.write_date).astimezone(event_tz)
        )
        event_data["created"] = vDatetime(
            utc.localize(self.create_date).astimezone(event_tz)
        )
        event_data["dtstart"] = vDatetime(utc.localize(self.start).astimezone(event_tz))
        event_data["dtend"] = vDatetime(utc.localize(self.stop).astimezone(event_tz))

    def _add_event_recurrence_id(self, event_data: dict) -> None:
        """Add the recurrence-id parameter to event data if self is linked
        to a calendar.recurrence record."""
        if self.recurrence_id:
            event_data["recurrence-id"] = vDatetime(self._get_ical_recurrence_id())

    def _add_event_recurrence(self, event_data: dict) -> None:
        """Add the recurrence rule (rrule) to event data if self is
        recurrent. This should only be called for base events."""
        if self.recurrence_id:
            rrule = str(self.recurrence_id._get_rrule())
            rrule_dict = _parse_rrule_string(rrule)
            if rrule_dict:
                event_data["rrule"] = vRecur(**rrule_dict)

    def _add_event_attendees(self, event_data: dict) -> None:
        """Add the attendee information to the "organizer" and "attendee"
        keys of the event data."""
        attendee_lines = []
        for partner in self.partner_ids:
            if partner == self.user_id.partner_id:
                continue
            attendee = vCalAddress(f"MAILTO:{partner.email}")
            attendee.params["cn"] = vText(partner.name)
            attendee_record = self.env["calendar.attendee"].search(
                [("event_id", "=", self.id), ("partner_id", "=", partner.id)],
                limit=1,
            )
            if attendee_record:
                attendee.params["partstat"] = vText(
                    self._map_attendee_status(attendee_record.state)
                )
            attendee_lines.append(attendee)
        organizer = vCalAddress(f"MAILTO:{self.user_id.email}")
        organizer.params["cn"] = self.user_id.name
        event_data["organizer"] = organizer
        event_data["attendee"] = attendee_lines

    @api.model
    def _html_to_text(self, html):
        return md(html, heading_style="ATX")

    @api.model
    def _map_attendee_status(self, state: str) -> str:
        """Map the state of an Odoo event attendee to its iCalendar
        equivalent.

        :param state: The state of the Odoo event attendee.
        :return: The equivalent iCalendar attendee state."""
        mapping = {
            "needsAction": "NEEDS-ACTION",
            "accepted": "ACCEPTED",
            "declined": "DECLINED",
            "tentative": "TENTATIVE",
        }
        return mapping.get(state, "NEEDS-ACTION")

    ###################################################################
    #### Methods for synchronizing changes from the server to Odoo ####
    ###################################################################

    @api.model
    def poll_caldav_server(self) -> None:
        """Poll each user's CalDAV calendar server for changes and
        synchronize them with their Odoo calendar."""
        all_users = self.env["res.users"].search([("is_caldav_enabled", "=", True)])
        for user in all_users:
            self.with_context(dont_notify=True)._poll_user_caldav_server(user)
            # self._poll_user_caldav_server(user)

    @api.model
    def _poll_user_caldav_server(self, user) -> None:
        """Poll a single user's CalDAV calendar on the server for changes
        and synchronize them to Odoo.

        :param user: The res.user record for whom to synchronize events.
        """
        _logger.info(f"Polling CalDAV server for user {user.name}")
        calendar = user._get_caldav_client().calendar(url=user.caldav_calendar_url)
        events = calendar.events()
        synced_events = self.env["calendar.event"]
        for caldav_event in events:
            ical_event = caldav_event.icalendar_instance
            synced_events |= self._sync_event_from_ical(ical_event, user)

        # TODO: check if this fails when the user is deleting someone else's event
        # TODO: check if we should send updates to invitees
        orphaned_events = self.search(
            [
                ("caldav_uid", "!=", False),
                ("id", "not in", synced_events.ids),
                ("user_id", "=", user.id),
            ]
        )
        orphaned_events = orphaned_events._to_sync()
        if orphaned_events:
            base_orphans = orphaned_events.filtered(
                lambda ev: ev.recurrence_id and ev.is_base_event
            )
            for base_orphan in base_orphans:
                try:
                    if calendar.event_by_uid(base_orphan.caldav_uid):
                        # There are some events remaining in this recurrence series,
                        # so we have synchronized them individually.
                        pass
                except NotFoundError:
                    # There are no more events with this UID, so we need to clear
                    # out the whole recurrence chain from the Odoo side.
                    ctx = {"caldav_no_sync": True}
                    recurrence = base_orphan.recurrence_id
                    recurrence.calendar_event_ids.with_context(**ctx).with_user(
                        user
                    ).unlink()
                    recurrence.with_context(**ctx).with_user(user).unlink()
            (orphaned_events - base_orphans).with_context(
                caldav_no_sync=True
            ).with_user(user).unlink()

    @api.model
    def _sync_event_from_ical(self, ical_event: icalendar.cal.Event, user: User):
        """Given an iCalendar event, compare the event with any existing
        Odoo event that it matches and synchronize the changes. If no event
        exists, create one iff the event is in the future.

        :param ical_event: The iCalendar event to synchronize with Odoo.
        :param user: The res.user record for whom to synchronize the event.
        :return: The calendar.event records that were synchronized.
        """
        synced_events = self.env["calendar.event"]
        event_components = [
            component for component in ical_event.walk() if component.name == "VEVENT"
        ]
        for component in event_components:
            uid = str(component.get("uid"))
            recurrence_id = (
                component.get("recurrence-id").dt
                if "recurrence-id" in component
                else None
            )

            existing_instance = self._get_existing_instance(uid, recurrence_id)
            outdated = self._get_outdated(component, existing_instance, synced_events)
            owned = (
                existing_instance and existing_instance.partner_id == user.partner_id
            )
            # Pass for_creation=True only when creating a new event
            values = self._get_values_from_ical_component(
                component, user, for_creation=not existing_instance
            )
            recurrency_vals = self._get_recurrency_values_from_ical_event(component)
            if not existing_instance:
                # If the event is in the past, we just ignore it.
                stop = values.get("stop")
                # Normalize date-only values to datetime for safe comparison
                if isinstance(stop, date) and not isinstance(stop, datetime):
                    stop = datetime.combine(stop, datetime.min.time())
                if stop and stop < datetime.now(tz=None):
                    continue
                # If we're creating an instance and it doesn't follow the recurrence,
                # just scrap the recurrency vals, they're not useful
                if not recurrency_vals.get("follow_recurrence"):
                    recurrency_vals = {}

                new_event = self.with_context(
                    caldav_no_sync=True, caldav_keep_ids=True
                ).create(values | recurrency_vals)
                self.env["calendar.event"].flush_model()
                if new_event.recurrency:
                    synced_events |= new_event.recurrence_id.calendar_event_ids
                else:
                    synced_events |= new_event
                continue
            elif outdated or not owned:
                pass
            else:
                changed_vals = existing_instance._get_recurrence_changes(
                    recurrency_vals
                ) | existing_instance._get_value_changes(values)
                if changed_vals:
                    existing_instance.with_context(
                        caldav_no_sync=True,
                        caldav_keep_ids=True,
                    ).write(changed_vals)

            if existing_instance.recurrency and existing_instance.is_base_event:
                synced_events |= existing_instance.recurrence_id.calendar_event_ids
            else:
                synced_events |= existing_instance
        return synced_events

    @api.model
    def _get_existing_instance(self, uid, recurrence_id: datetime | None):
        """Find the Odoo calendar.event record matching uid and,
        if set, recurrence_id.
        """
        if recurrence_id:
            recurrence_id = recurrence_id.astimezone(utc).replace(tzinfo=None)
            instance = self.env["calendar.event"].search(
                [
                    ("caldav_uid", "=", uid),
                    ("caldav_recurrence_id", "=", recurrence_id),
                ]
            )
        else:
            instance = self.env["calendar.event"].search(
                [
                    ("caldav_uid", "=", uid),
                    ("recurrency", "=", False),
                ]
            )
            if instance:
                return instance
            else:
                return (
                    self.env["calendar.recurrence"]
                    .search(
                        [
                            ("base_event_id.caldav_uid", "=", uid),
                        ]
                    )
                    .base_event_id
                )

        if len(instance) == 1:
            return instance
        if len(instance) > 1:
            instance = instance.recurrence_id.base_event_id

        return instance or self.env["calendar.event"].search(
            [
                ("caldav_uid", "=", uid),
                ("recurrence_id", "=", False),
            ]
        )

    @api.model
    def _get_recurrency_values_from_ical_event(
        self, component: icalendar.cal.Component
    ) -> dict:
        """Match calendar.event recurring fields to RRULE fields.

        See https://icalendar.org/iCalendar-RFC-5545/3-8-5-3-recurrence-rule.html
        """
        rrule = [item[1] for item in component.property_items() if item[0] == "RRULE"]
        rrule = rrule[0] if rrule else None

        if component.get("recurrence-id"):
            # When a component has "recurrence-id" set, it is a single event
            # in a series of events. Recurrence-id is the time the event should
            # normally occur at if it follows the recurrence of the series.
            follows_recurrence = (
                component.get("recurrence-id").dt == component.get("dtstart").dt
            )
            if not follows_recurrence:
                return {
                    "follow_recurrence": False,
                    "recurrence_update": "self_only",
                }
            if not rrule:
                # This event is following the base event's recurrence rule
                return {
                    "follow_recurrence": True,
                    "recurrence_update": "self_only",
                }

        if not rrule or not isinstance(rrule, vRecur):
            return {}
        until = rrule.get("until")
        if until and isinstance(until, list):
            until = until[0].astimezone(utc)
        rrule_str = rrule.to_ical() and rrule.to_ical().decode("utf-8")
        if rrule_str:
            dtstart = component.get(
                "dtstart"
            ).dt  # Sometimes a date, sometimes a datetime
            if hasattr(dtstart, "astimezone"):
                dtstart = dtstart.astimezone(utc)
            rrule_params = self.env["calendar.recurrence"]._rrule_parse(
                "RRULE:" + rrule_str, dtstart
            )
        else:
            _logger.debug(f"Could not convert RRULE to string: {rrule}")
            return {}

        vals = {
            "recurrency": True,
            "follow_recurrence": True,
            "recurrence_update": "future_events",
            **rrule_params,
        }
        # Convert None to False since unfilled Odoo fields come back False
        vals = {
            key: value if value is not None else False for key, value in vals.items()
        }

        # Forever doesn't exist in Odoo. The calendar.recurrence model changes 'forever'
        # into 'count' with MAX_RECURRENT_EVENT as the 'count' parameter
        if vals.get("end_type") == "forever":
            vals.update(end_type="count")
            if not vals.get("count"):
                vals.update(count=MAX_RECURRENT_EVENT)
        until = vals.get("until")
        if until and (isinstance(until, vDatetime) or isinstance(until, vDate)):
            until_day = until.dt if isinstance(until, vDatetime) else until.dt
            vals.update(until=until_day)
            vals.pop("count", None)
        return vals

    def _get_recurrence_changes(self, recurrency_vals: dict) -> dict:
        """Compare a set of recurrency values with those already present on
        this event.

        :param recurrency_vals: The recurrency values from an iCalendar event
        to compare to self.

        :return: A dictionary containing only the values that are different
        from those in self."""
        if not recurrency_vals and not self.recurrence_id:
            return {}
        if not recurrency_vals and self.recurrence_id:
            return {"recurrence_update": "all_events", "recurrency": False}
        if recurrency_vals and not self.recurrence_id:
            return recurrency_vals
        changed_fields = {
            key: recurrency_vals[key]
            for key in recurrency_vals.keys()
            if hasattr(self, key) and recurrency_vals[key] != getattr(self, key)
        }
        if len(changed_fields) == 1 and "recurrence_update" in changed_fields:
            return {}
        return changed_fields

    def _get_value_changes(self, values: dict) -> dict:
        """Compare the values from an iCalendar event to those already
        present on self.

        :param values: The values from an iCalendar event
        :return: A dictionary containing only the values that are different
        from those in self."""
        changed_vals = {}
        # Don't update partner_ids if no change
        if "partner_ids" in values:
            partner_ids = values["partner_ids"][0][2]  # this is a SET command
            added_partner_ids = set(
                [id for id in partner_ids if id not in self.partner_ids.ids]
            )
            removed_partner_ids = set(
                [id for id in self.partner_ids.ids if id not in partner_ids]
            )
            if not (added_partner_ids or removed_partner_ids):
                values.pop("partner_ids")  # They break the equality check later
            else:
                changed_vals["partner_ids"] = values["partner_ids"]

        # Get just the list of values that have changed, leave the others alone
        for key, val in values.items():
            curr_val = getattr(self, key)
            # Can't deal with x2many fields, need ID from a record
            if isinstance(val, list):
                continue
            if curr_val and isinstance(curr_val, models.Model):
                if len(curr_val) > 1:
                    continue
                curr_val = curr_val.id
            if curr_val != val:
                changed_vals.update({key: val})
        return changed_vals

    @api.model
    def _get_outdated(
        self,
        component: icalendar.cal.Component,
        existing_instance: OdooCalendarEvent,
        synced_events: OdooCalendarEvent,
    ) -> bool:
        """Check whether a component from the CalDAV server (typically an
        event) is outdated when compared to its existing Odoo calendar.event
        instance.

        :param component: The iCalendar component to check.
        :param existing_instance: The calendar.event record to
        compare with.
        :param synced_events: The calendar.event record(s) that have already
        been synchronized.
        :return: True if the iCalendar component is outdated, False otherwise.
        """
        outdated = False
        last_modified = component.get("dtstamp") and component.get("dtstamp").dt
        if (
            existing_instance
            and last_modified
            and existing_instance not in synced_events
        ):
            # Ensure both datetimes are timezone-aware for comparison
            write_date = utc.localize(existing_instance.write_date)
            if last_modified.tzinfo is None:
                last_modified = utc.localize(last_modified)
            if last_modified < write_date:
                outdated = True
        return outdated

    @api.model
    def _get_values_from_ical_component(
        self, component: icalendar.cal.Component, user: User, for_creation: bool = False
    ) -> dict:
        """Get the dictionary representing calendar.event field values from
        an iCalendar event.

        :param component: The iCalendar component from which to extract values.
        :param user: The res.users record the event will belong to.
        :param for_creation: Whether these values are for creating a new event (True)
                            or updating an existing one (False).
        :return: The dictionary of values to construct a calendar.event."""
        start = component.get("dtstart") and component.decoded("dtstart")
        if isinstance(start, datetime):
            start = start.astimezone(utc).replace(tzinfo=None)
        end = component.get("dtend") and component.decoded("dtend")
        if isinstance(end, datetime):
            end = end.astimezone(utc).replace(tzinfo=None)

        # Get attendees regardless of creation/update
        attendee_ids = self._get_attendee_partners(component, user.partner_id.email)

        # Basic values that apply to both creation and updates
        values = {
            "name": str(component.get("summary")),
            "start": start,
            "stop": end,
            "description": self._text_to_html(
                self._extract_component_text(component, "description")
            ),
            "location": self._extract_component_text(component, "location"),
            "videocall_location": self._extract_component_text(component, "conference"),
            "caldav_uid": str(component.get("uid")),
            "partner_ids": [(6, 0, attendee_ids.ids)],
        }

        # Only set user_id and partner_id during creation
        if for_creation:
            organizer_partner = self._get_organizer_partner(component)
            if organizer_partner:
                # Get the Odoo user ID associated with the organizer partner
                organizer = (
                    organizer_partner.user_ids[0].id
                    if organizer_partner.user_ids
                    else False
                )
                values.update(
                    {
                        "partner_id": organizer_partner.id,
                        "user_id": organizer,
                    }
                )
            else:
                # For new events without an organizer, use the current user
                values.update(
                    {
                        "partner_id": user.partner_id.id,
                        "user_id": user.id,
                    }
                )

        return values

    @api.model
    def _get_attendee_partners(
        self, component: icalendar.cal.Component, current_user_email: str
    ) -> Partner:
        """Get the res.partner records who are attendees for a given
        iCalendar event.

        :param component: The iCalendar component from which to extract
        attendees.
        :param current_user_email: The email for the res.users record the
        matching Odoo event belongs to.
        :return: The res.partner records who are attendees for the event."""
        attendee_emails = self._get_ical_attendee_emails(component)
        # Add organizer to attendees if present
        organizer = component.get("organizer")
        if organizer:
            organizer_email = _extract_vcal_email(organizer)
            if organizer_email not in attendee_emails:
                attendee_emails.append(organizer_email)
        # Add current user if not already in attendees
        if current_user_email not in attendee_emails:
            attendee_emails.append(current_user_email)
        existing_partners = self.env["res.partner"].search(
            [("email", "in", attendee_emails)]
        )
        missing_emails = [
            email
            for email in attendee_emails
            if email not in [partner.email for partner in existing_partners]
        ]
        # Create new partners without triggering notifications
        added_partners = (
            self.env["res.partner"]
            .with_context(
                mail_notify_author=False,  # Don't notify the author
                mail_notify_force_send=True,  # Don't force send notifications
                tracking_disable=True,  # Disable tracking
                no_reset_password=True,  # Don't trigger password reset emails
            )
            .create(
                [
                    {
                        "name": email,
                        "email": email,
                    }
                    for email in missing_emails
                ]
            )
        )
        final_attendees = {}
        all_partners = existing_partners | added_partners
        # We do this because partners may have identical emails and we only want one
        # attending partner per email. Otherwise invitations get sent out multiple times
        # and nobody likes that.
        # Prioritize users as attendees
        for partner in all_partners.filtered(lambda partner: bool(partner.user_id)):
            if partner.email not in final_attendees:
                final_attendees[partner.email] = partner.id

        for partner in all_partners.filtered(lambda partner: not partner.user_id):
            if partner.email not in final_attendees:
                final_attendees[partner.email] = partner.id

        return all_partners.filtered(
            lambda partner: partner.id in final_attendees.values()
        )

    @api.model
    def _get_organizer_partner(self, component: icalendar.cal.Component) -> Partner:
        """Get the partner matching the organizer on an iCalendar event.

        :param component: The iCalendar component from which to extract the
        organizer.
        :return: The res.partner record matching the event organizer."""

        organizer = component.get("organizer")
        if organizer:
            email = _extract_vcal_email(organizer)
            _logger.info("Organizer email: %s", email)
            partner = self.env["res.partner"].search([("email", "=", email)], limit=1)
            _logger.info("Found partner: %s", partner)
            if not partner:
                # Create new partner without triggering notifications
                partner = (
                    self.env["res.partner"]
                    .with_context(
                        mail_notify_author=False,
                        mail_notify_force_send=True,
                        tracking_disable=True,
                        no_reset_password=True,
                    )
                    .create(
                        {
                            "name": email,
                            "email": email,
                        }
                    )
                )
                _logger.info("Created partner: %s", partner)
            return partner
        else:
            return self.env["res.partner"]

    @api.model
    def _get_ical_attendee_emails(
        self, component: icalendar.cal.Component
    ) -> list[str]:
        """Get the email addresses for attendees from an iCalendar event.

        :param component: The iCalendar event from which to extract emails.
        :return: A list of attendee emails
        """
        attendees = component.get("attendee", [])
        if not isinstance(attendees, list):
            attendees = [attendees]
        attendee_emails = [_extract_vcal_email(attendee) for attendee in attendees]
        return attendee_emails

    @api.model
    def _extract_component_text(
        self, component: icalendar.cal.Component, subcomponent_name: str
    ) -> str:
        """Extract the text from an iCalendar subcomponent. Convenience
        method to deal with empty subcomponents.

        :param component: The iCalendar component from which to extract text.
        :param subcomponent_name: The name of the subcomponent to extract.
        :return: The extracted subcomponent text or an empty string.
        """
        val = component.get(subcomponent_name)
        text = str(val) if val else ""
        return text

    @api.model
    def _text_to_html(self, text):
        return md2.markdown(text)
