# Copyright 2026 XtremXpert
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    public_holiday_line_id = fields.Many2one(
        comodel_name="calendar.public.holiday.line",
        string="Public Holiday",
        ondelete="cascade",
        index=True,
    )
