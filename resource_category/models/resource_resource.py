# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    resource_category_ids = fields.Many2many(
        "resource.category",
        string="Categories",
    )
