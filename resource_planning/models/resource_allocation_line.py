# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ResourceAllocationLine(models.Model):
    _name = 'resource.allocation.line'
    _description = 'Resource Allocation Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    plan_id = fields.Many2one(
        string='Plan',
        comodel_name='resource.allocation.plan',
        required=True,
        ondelete='cascade',
    )
