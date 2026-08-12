# Copyright 2026 Thierry Leblanc
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class CalendarAttendee(models.Model):
    _inherit = "calendar.attendee"

    def _compute_mail_tz(self):
        """Autofix tz from related resource booking.

        Any notification related to a resource.booking must be emitted in the
        same TZ as the resource.booking. Otherwise it's confusing to the user.

        In v18 this was done by overriding calendar.event.get_interval(), which
        no longer exists in v19: the invitation template now resolves the
        timezone from calendar.attendee.mail_tz.
        """
        res = super()._compute_mail_tz()
        for attendee in self:
            booking = attendee.event_id.sudo().resource_booking_ids
            booking_tz = booking.type_id.resource_calendar_id.tz
            if booking_tz:
                attendee.mail_tz = booking_tz
        return res
