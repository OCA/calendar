# Copyright 2023 Le Filament
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.osv import expression


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    def _get_microsoft_sync_domain(self):
        domain = super()._get_microsoft_sync_domain()
        ICP = self.env["ir.config_parameter"].sudo()
        sync_option = ICP.get_param("microsoft_calendar_sync_option", default="all")
        if sync_option == "future":
            index = None
            for i, arg in enumerate(domain):
                if (
                    not isinstance(arg, str)
                    and isinstance(arg[0], str)
                    and arg[0] == "stop"
                ):
                    index = i
            if index:
                domain[index] = ("stop", ">", fields.Datetime.now())
        elif sync_option == "none":
            domain = expression.AND([domain, [("id", "=", False)]])
        return domain
