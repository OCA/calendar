# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


class RBCWizardCategory(models.TransientModel):
    _name = "rbc.wizard.category"
    _description = "Resource Booking Combination Wizard Category"
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
    selected_resource_ids = fields.Many2many(
        "rbc.wizard.resource",
        string="Resources",
    )
    available_resource_ids = fields.One2many(
        "rbc.wizard.resource",
        "rbc_wizard_category_id",
        "Available Resources",
    )
