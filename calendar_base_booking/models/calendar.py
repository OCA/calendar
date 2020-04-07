# Copyright 2020 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    booking_type = fields.Selection(
        [
            ("bookable", "Bookable"),
            ("not_bookable", "Not bookable"),
            ("booked", "Booked"),
        ]
    )
