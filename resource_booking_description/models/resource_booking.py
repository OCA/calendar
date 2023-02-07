# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


class ResourceBooking(models.Model):
    _inherit = "resource.booking"

    description = fields.Text("Description")
