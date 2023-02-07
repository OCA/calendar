# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


class ResourceBooking(models.Model):
    _inherit = "resource.booking"

    # fixme: store this in the meeting instead of in the booking (see roadmap)
    number_of_attendees = fields.Integer("Number of Attendees", default=1)
