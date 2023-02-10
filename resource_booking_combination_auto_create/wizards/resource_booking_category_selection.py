# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


class ResourceBookingCategorySelection(models.TransientModel):
    _name = "resource.booking.category.selection"
    _description = "Resource Booking Category Selection"
    _table = "rb_category_selection"
    _order = "name"

    name = fields.Char(related="resource_category_id.name", store=True)
    resource_booking_combination_wizard_id = fields.Many2one(
        "resource.booking.combination.wizard",
        "Resource Booking Combination Wizard",
        required=True,
        ondelete="cascade",
    )
    resource_category_id = fields.Many2one(
        "resource.category",
        "Resource Category",
        required=True,
        ondelete="cascade",
    )
    resource_ids = fields.Many2many(
        "resource.booking.category.selection.resource",
        string="Resources",
    )
    available_resource_ids = fields.One2many(
        "resource.booking.category.selection.resource",
        "resource_booking_category_selection_id",
        "Available Resources",
    )
