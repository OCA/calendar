# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResourceBookingCombinationRel(models.Model):
    _name = "resource.booking.type.combination.rel"
    _description = "Resource booking type relation with combinations"
    _order = "sequence"
    _rec_name = "combination_id"

    sequence = fields.Integer(index=True, required=True, default=100)
    combination_id = fields.Many2one(
        "resource.booking.combination",
        string="Combination",
        index=True,
        required=True,
        ondelete="cascade",
    )
    type_id = fields.Many2one(
        "resource.booking.type",
        string="Type",
        index=True,
        required=True,
        ondelete="cascade",
    )
    type_name = fields.Char(related="type_id.name")
