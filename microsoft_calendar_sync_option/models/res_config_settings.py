# Copyright 2023 Le Filament
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cal_microsoft_sync_option = fields.Selection(
        selection=[
            ("all", "All events"),
            ("future", "Only future events"),
            ("none", "No event"),
        ],
        string="Calendar synchronization option",
        help="Odoo to Outlook events synchronization",
        config_parameter="microsoft_calendar_sync_option",
        default="all",
    )
