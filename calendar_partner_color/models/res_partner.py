# Copyright (C) 2021 raphael.reverdy@akretion.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from random import randint

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_default_color(self):
        return randint(0, 29)

    color = fields.Integer(default=_get_default_color)
