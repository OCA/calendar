# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    resource_planning_timespan = fields.Selection(
        string='Resource Planning Timespan',
        selection=[
            ('day', 'Day'),
            ('week', 'Week'),
            ('month', 'Month'),
        ],
        default='month',
        required=True,
        help=(
            'Resource allocation plan can cover a day, a week, or an entire'
            ' month.'
        ),
    )
    resource_planning_uom = fields.Selection(
        string='Resource Planning Time Unit',
        selection=[
            ('hour', 'Hours'),
            ('day', 'Days'),
        ],
        default='day',
        required=True,
        help=(
            'Resource planning duration can be expressed in hours or in days'
        ),
    )
