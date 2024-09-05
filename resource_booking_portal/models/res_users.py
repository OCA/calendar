# Copyright 2024 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    create_booking_from_portal = fields.Boolean(
        string="Create booking from portal",
    )
    is_portal_user = fields.Boolean(compute="_compute_is_portal_user")

    def _compute_is_portal_user(self):
        for record in self:
            record.is_portal_user = record.has_group("base.group_portal")
