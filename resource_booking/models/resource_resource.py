# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    @api.constrains("calendar_id", "resource_type", "tz", "user_id")
    def _check_bookings_scheduling(self):
        """Scheduled bookings must have no conflicts."""
        bookings = self.env["resource.booking"].search(
            [("combination_id.resource_ids", "in", self.ids)]
        )
        return bookings._check_scheduling()
