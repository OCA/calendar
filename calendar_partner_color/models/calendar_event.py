# Copyright (C) 2021 raphael.reverdy@akretion.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    color = fields.Integer(related="user_id.color")
