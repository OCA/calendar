# Copyright 2023 Le Filament
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.osv import expression


class RecurrenceRule(models.Model):
    _inherit = "calendar.recurrence"

    def _get_microsoft_sync_domain(self):
        domain = super()._get_microsoft_sync_domain()
        ICP = self.env["ir.config_parameter"].sudo()
        sync_option = ICP.get_param("microsoft_calendar_sync_option", default="all")
        if sync_option == "none":
            domain = expression.AND([domain, [("id", "=", False)]])
        return domain
