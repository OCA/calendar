# Copyright 2019 ACSONE SA/NV
# Copyright 2024 INVITU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class Picking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "calendar.event.link.mixin"]
