# Copyright 2020 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    booking_type = fields.Selection(
        [
            ("bookable", "Bookable"),
            ("not_bookable", "Not bookable"),
            ("booked", "Booked"),
        ]
    )

    @api.onchange("booking_type")
    def on_booking_type_change(self):
        if self.booking_type in ["bookable", "not_bookable"]:
            self.name = dict(
                self._fields["booking_type"]._description_selection(self.env)
            )[self.booking_type]
        else:
            self.name = ""
