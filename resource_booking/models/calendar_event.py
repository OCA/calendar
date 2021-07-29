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

    def unlink(self, can_be_deleted=True):
        """Check you're allowed to unschedule it."""
        self._validate_booking_modifications()
        return super().unlink(can_be_deleted=can_be_deleted)

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

    def create_attendees(self):
        """Autoconfirm resource attendees if preselected."""
        old_attendees = self.attendee_ids
        result = super(
            # This context avoids sending invitations to new attendees
            CalendarEvent,
            self.with_context(detaching=True),
        ).create_attendees()
        new_attendees = (self.attendee_ids - old_attendees).with_context(
            self.env.context
        )
        for attendee in new_attendees:
            # No need to change state if it's already done
            if attendee.state in {"accepted", "declined"}:
                continue
            rb = attendee.event_id.resource_booking_ids
            # Confirm requester attendee always if requested
            if (
                self.env.context.get("autoconfirm_booking_requester")
                and attendee.partner_id == rb.partner_id
            ):
                attendee.state = "accepted"
                continue
            # Auto-confirm if attendee comes from a handpicked combination
            if rb.combination_auto_assign:
                continue
            if attendee.partner_id in rb.combination_id.resource_ids.user_id.partner_id:
                attendee.state = "accepted"
        # Send invitations like upstream would have done
        to_notify = new_attendees.filtered(lambda a: a.email != self.env.user.email)
        if to_notify and not self.env.context.get("detaching"):
            to_notify._send_mail_to_attendees(
                "calendar.calendar_template_meeting_invitation"
            )
        return result

    def get_interval(self, interval, tz=None):
        """Autofix tz from related resource booking.

        This function is called to render calendar.event notification mails.
        Any notification related to a resource.booking must be emitted in the
        same TZ as the resource.booking. Otherwise it's confusing to the user.
        """
        tz = self.resource_booking_ids.type_id.resource_calendar_id.tz or tz
        return super().get_interval(interval=interval, tz=tz)
