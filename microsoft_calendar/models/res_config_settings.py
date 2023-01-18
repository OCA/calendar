# flake8: noqa
# pylint: skip-file
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cal_microsoft_client_id = fields.Char(
        "Microsoft Client_id",
        config_parameter="microsoft_calendar_client_id",
        default="",
    )
    cal_microsoft_client_secret = fields.Char(
        "Microsoft Client_key",
        config_parameter="microsoft_calendar_client_secret",
        default="",
    )
    module_microsoft_calendar = fields.Boolean("Outlook Calendar",)
