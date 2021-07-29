# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from pytz import UTC

from odoo import api, fields, models

from odoo.addons.calendar.models.calendar import calendar_id2real_id
from odoo.addons.resource.models.resource import Intervals


class Busy(Exception):
    pass  # This is not a real exception, just a helper


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    @api.constrains("attendance_ids", "global_leave_ids", "leave_ids", "tz")
    def _check_bookings_scheduling(self):
        """Scheduled bookings must have no conflicts."""
        bookings = self.env["resource.booking"].search(
            [
                ("state", "=", "confirmed"),
                ("stop", ">=", fields.Datetime.now()),
                "|",
                ("combination_id.forced_calendar_id", "in", self.ids),
                ("combination_id.resource_ids.calendar_id", "in", self.ids),
            ]
        )
        return bookings._check_scheduling()

    @api.model
    def _calendar_event_busy_intervals(
        self, start_dt, end_dt, resource, analyzed_booking_id
    ):
        """Get busy meeting intervals."""
        assert start_dt.tzinfo
        assert end_dt.tzinfo
        start_dt, end_dt = (
            fields.Datetime.to_string(dt.astimezone(UTC)) for dt in (start_dt, end_dt)
        )
        intervals = []
        resource_user = (
            resource.resource_type == "user"
            and resource.user_id.active
            and resource.user_id
        )
        # Simple domain to get all possibly conflicting events in a single
        # query; this reduces DB calls and helps the underlying recurring
        # system (in calendar.event) to work smoothly
        all_events = (
            self.env["calendar.event"]
            .with_context(active_test=True)
            .search([("start", "<=", end_dt), ("stop", ">=", start_dt)])
        )
        for event in all_events:
            real_event = self.env["calendar.event"].browse(
                calendar_id2real_id(event.id)
            )
            # Is the event the same one we're currently checking?
            if real_event.resource_booking_ids.id == analyzed_booking_id:
                continue
            try:
                # Is the event not booking our resource?
                if resource & real_event.mapped(
                    "resource_booking_ids.combination_id.resource_ids"
                ):
                    raise Busy
                # Special cases when the booked resource is a person
                if resource_user:
                    # Is it a busy event belonging to the resource?
                    if event.user_id == resource_user and event.show_as == "busy":
                        raise Busy
                    # ... or is he invited to this event?
                    for attendee in event.attendee_ids:
                        if (
                            attendee.partner_id == resource_user.partner_id
                            and attendee.state != "declined"
                        ):
                            raise Busy
            except Busy:
                # Add the matched event as a busy interval
                intervals.append(
                    (
                        fields.Datetime.context_timestamp(
                            event, fields.Datetime.to_datetime(event.start)
                        ),
                        fields.Datetime.context_timestamp(
                            event, fields.Datetime.to_datetime(event.stop)
                        ),
                        self.env["resource.calendar.leaves"],
                    )
                )
        return Intervals(intervals)

    def _leave_intervals_batch(
        self, start_dt, end_dt, resources=None, domain=None, tz=None
    ):
        """Count busy meetings as leaves if required by context."""
        result = super()._leave_intervals_batch(start_dt, end_dt, resources, domain, tz)
        if self.env.context.get("analyzing_booking"):
            for resource_id in result:
                # TODO Make this work in batch too
                result[resource_id] |= self._calendar_event_busy_intervals(
                    start_dt,
                    end_dt,
                    self.env["resource.resource"].browse(resource_id),
                    self.env.context["analyzing_booking"],
                )
        return result
