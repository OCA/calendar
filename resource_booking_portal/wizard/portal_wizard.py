# Copyright 2024 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PortalWizardUser(models.TransientModel):
    _inherit = "portal.wizard.user"

    booking_from_portal = fields.Boolean("Booking from portal")

    def _create_user(self):
        res = super()._create_user()
        res.write({"create_booking_from_portal": self.booking_from_portal})
        return res
