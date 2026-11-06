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
            # Plain calendar events have no booking: keep the attendee's own
            # timezone instead of failing on an empty recordset.
            booking_type = attendee.event_id.sudo().resource_booking_ids.type_id[:1]
            if booking_type:
                attendee.mail_tz = booking_type._booking_timezone()
        return res
