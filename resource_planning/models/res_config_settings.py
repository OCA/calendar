# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    resource_planning_timespan = fields.Selection(
        string='Timespan',
        related='company_id.resource_planning_timespan',
        readonly=False,
    )
    resource_planning_uom = fields.Selection(
        string='Time Unit',
        related='company_id.resource_planning_uom',
        readonly=False,
    )
