# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


class RBCWizardResource(models.TransientModel):
    _name = "rbc.wizard.resource"
    _description = "Resource Booking Combination Wizard Resource"
    _order = "name"

    name = fields.Char(related="resource_id.name", store=True)
    rbc_wizard_category_id = fields.Many2one(
        "rbc.wizard.category",
        "Resource Booking Combination Wizard Category Selection",
        required=True,
        ondelete="cascade",
    )
    resource_id = fields.Many2one(
        "resource.resource",
        "Resource",
        required=True,
        ondelete="cascade",
    )
    # this field is only needed for searching
    selected_from = fields.Many2many("rbc.wizard.category")
