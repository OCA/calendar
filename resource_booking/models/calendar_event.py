# Copyright 2021 Tecnativa - Jairo Llopis
# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CalendarEvent(models.Model):
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
        bookings = self.sudo().resource_booking_ids
        return bookings._check_scheduling()

    def _validate_booking_modifications(self):
        """Make sure you can cancel a booking meeting."""
        bookings = self.sudo().resource_booking_ids
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

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        """If we are creating the calendar event from the resource booking
        (detected from the resource_booking_event context key), we need to
        inject the standard mail context `mail_notify_author` to super to get
        the own author notified when someone books a reservation, but only
        in the case that the mail is being sent to them, as if not the author
        may receive one copy per each of the attendees. This happens only when
        the the subtype not is enabled by default in the instance.
        """
        if self.env.context.get("resource_booking_event") and msg_vals.get(
            "author_id"
        ) in msg_vals.get("partner_ids", []):
            self = self.with_context(mail_notify_author=True)
        return super()._notify_thread(message=message, msg_vals=msg_vals, **kwargs)

    def _notify_get_recipients(self, message, msg_vals, **kwargs):
        """If we are creating the calendar event from resource booking, we want to
        notify only the partner_ids and not all the followers (to avoid that each email
        is sent to all followers). Example: Resource booking with combination of several
        users. This only happens when the subtype note is enabled by default in the
        instance.
        """
        res = super()._notify_get_recipients(
            message=message, msg_vals=msg_vals, **kwargs
        )
        if self.env.context.get("resource_booking_event"):
            res2 = []
            partner_ids = msg_vals.get("partner_ids", [])
            for item in res:
                if item["id"] in partner_ids:
                    res2.append(item)
            return res2
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Transfer resource booking to _attendees_values by context.

        We need to serialize the creation in that case.
        resource_booking_event custom key from context is necessary.
        We cannot use mail_notify_author key in the context because if the mail_note
        subtype is set by default, the email of each attendee would be sent also to
        the author (example: a meeting with 2 attendees would send 2 emails but
        each of them would be sent to the partner of the attendee + author of
        the email).
        """
        vals_list2 = []
        records = self.env["calendar.event"]
        for vals in vals_list:
            if "resource_booking_ids" in vals:
                records += super(
                    CalendarEvent,
                    self.with_context(
                        resource_booking_ids=vals["resource_booking_ids"],
                        resource_booking_event=True,
                    ),
                ).create(vals)
            else:
                vals_list2.append(vals)
        records += super().create(vals_list2)
        return records

    def get_interval(self, interval, tz=None):
        """Autofix tz from related resource booking.

        This function is called to render calendar.event notification mails.
        Any notification related to a resource.booking must be emitted in the
        same TZ as the resource.booking. Otherwise it's confusing to the user.
        """
        tz = self.resource_booking_ids.type_id.resource_calendar_id.tz or tz
        return super().get_interval(interval=interval, tz=tz)

    def _attendees_values(self, partner_commands):
        """Autoconfirm resource attendees if preselected and hand-picked on RB.

        NOTE: There's no support for changing `resource_booking_ids` once the meeting
        is created nor having more than one Rb attached to the same meeting, but that's
        not a real case for now.
        """
        attendee_commands = super()._attendees_values(partner_commands)
        partner_ids = False
        for cmd in self.env.context.get("resource_booking_ids", []):
            if cmd[0] == 0 and not cmd[2].get("combination_auto_assign", True):
                partner_ids = [cmd[2]["partner_id"]]
            elif cmd[0] == 6:
                rb = self.env["resource.booking"].browse(cmd[2])
                if rb.combination_auto_assign:
                    continue  # only auto-confirm if handpicked combination
                partner_ids = rb.combination_id.resource_ids.user_id.partner_id.ids
        for command in attendee_commands:
            if command[0] != 0:
                continue
            if not partner_ids:
                rb = self.sudo().resource_booking_ids
                partner_ids = rb.combination_id.resource_ids.user_id.partner_id.ids
            if command[2]["partner_id"] in partner_ids:
                command[2]["state"] = "accepted"
        return attendee_commands
