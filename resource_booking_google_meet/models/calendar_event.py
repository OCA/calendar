# Copyright 2026 Ledo Enterprises - D. Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    def write(self, vals):
        # Capture events that are about to receive a Google Meet URL for the first time.
        # Must run before super() so we can compare old vs new videocall_location.
        to_notify = self.env["calendar.event"]
        if "meet.google.com" in (vals.get("videocall_location") or ""):
            to_notify = self.filtered(
                lambda e: "meet.google.com" not in (e.videocall_location or "")
            )
        result = super().write(vals)
        if to_notify:
            template = self.env.ref(
                "resource_booking_google_meet.mail_template_meet_link",
                raise_if_not_found=False,
            )
            if template:
                bookings = self.env["resource.booking"].search(
                    [("meeting_id", "in", to_notify.ids)]
                )
                for booking in bookings:
                    template.send_mail(booking.id, force_send=True)
        return result
