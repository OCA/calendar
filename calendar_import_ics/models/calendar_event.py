# Copyright (C) 2024 - ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"
    event_identifier = fields.Char("Event Id")
