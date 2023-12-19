# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


class ResourceCategory(models.Model):
    _name = "resource.category"
    _description = "Resource Category"
    _order = "name"

    name = fields.Char(required=True)
    resource_ids = fields.Many2many("resource.resource", string="Resources")
