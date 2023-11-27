# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CalendarEvent(models.Model):
    _name = "calendar.event"
    _inherit = "calendar.event"

    # One2one field, actually
    resource_booking_ids = fields.One2many(
        comodel_name="resource.booking",
        inverse_name="meeting_id",
        string="Resource booking",
    )

    @api.constrains("resource_booking_ids", "start", "stop")
    def _check_bookings_scheduling(self):
        """Scheduled bookings must have no conflicts."""
        bookings = self.mapped("resource_booking_ids")
        return bookings._check_scheduling()

    def _validate_booking_modifications(self):
        """Make sure you can cancel a booking meeting."""
        bookings = self.mapped("resource_booking_ids")
        modifiable = bookings.filtered("is_modifiable")
        frozen = bookings - modifiable
        if frozen:
            raise ValidationError(
                _(
                    "You are not allowed to alter these bookings because "
                    "they exceeded their modification deadlines:\n\n- %s"
                )
                % "\n- ".join(frozen.mapped("display_name"))
            )

    def unlink(self):
        """Check you're allowed to unschedule it."""
        self._validate_booking_modifications()
        return super().unlink()

    def write(self, vals):
        """Check you're allowed to reschedule it."""
        before = [(one.start, one.stop) for one in self]
        result = super().write(vals)
        rescheduled = self
        for (old_start, old_stop), new in zip(before, self):
            if old_start == new.start and old_stop == new.stop:
                rescheduled -= new
        rescheduled._validate_booking_modifications()
        return result

    def get_interval(self, interval, tz=None):
        """Autofix tz from related resource booking.

        This function is called to render calendar.event notification mails.
        Any notification related to a resource.booking must be emitted in the
        same TZ as the resource.booking. Otherwise it's confusing to the user.
        """
        tz = self.resource_booking_ids.type_id.resource_calendar_id.tz or tz
        return super().get_interval(interval=interval, tz=tz)
