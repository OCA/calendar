# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


class ResourceBookingCategorySelectionResource(models.TransientModel):
    _name = "resource.booking.category.selection.resource"
    _description = "Resource Booking Category Selection Resource"
    _table = "rb_category_selection_resource"
    _order = "name"

    name = fields.Char(related="resource_id.name", store=True)
    resource_booking_category_selection_id = fields.Many2one(
        "resource.booking.category.selection",
        "Resource Booking Category Selection",
        required=True,
        ondelete="cascade",
    )
    resource_id = fields.Many2one(
        "resource.resource",
        "Resource",
        required=True,
        ondelete="cascade",
    )
