# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta, MO, SU

from odoo import api, fields, models, _


class ResourceAllocationPlan(models.Model):
    _name = 'resource.allocation.plan'
    _description = 'Resource Allocation Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        compute='_compute_name',
        context_dependent=True,
    )
    state = fields.Selection(
        string='Status',
        selection=lambda self: self._get_state_selection(),
        default='draft',
        readonly=True,
        copy=False,
        track_visibility='onchange',
    )
    timespan_since = fields.Date(
        string='Start Date',
        default=lambda self: self._default_timespan_since(),
        required=True,
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    timespan_until = fields.Date(
        string='End Date',
        default=lambda self: self._default_timespan_until(),
        required=True,
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    # timespan_until = fields.Date(
    #     string='Timespan',
    #     default=lambda self: self._default_timespan_until(),
    #     required=True,
    #     copy=False,
    #     readonly=True,
    #     states={'draft': [('readonly', False)]},
    # )
    line_ids = fields.One2many(
        string='Lines',
        comodel_name='resource.allocation.line',
        inverse_name='plan_id',
        copy=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
    )

    @api.model
    def _get_state_selection(self):
        selection = []
        selection.append(('draft', 'Draft'))
        selection.extend(self._get_state_selection_transient())
        selection.append(('confirmed', 'Confirmed'))
        return selection

    @api.model
    def _get_state_selection_transient(self):
        """Extension hook for various validation approaches"""
        return []

    @api.model
    def _default_timespan_since(self):
        timespan = self.env.user.company_id.resource_planning_timespan
        timespan_since = self.context.get(
            'default_timespan_since',
            fields.Date.today()
        )
        if timespan == 'week':
            timespan_since += relativedelta(weekday=MO(-1))
        elif timespan == 'month':
            timespan_since += relativedelta(day=1)
        return timespan_since

    @api.model
    def _default_timespan_until(self):
        timespan = self.env.user.company_id.resource_planning_timespan
        timespan_until = self.context.get(
            'default_timespan_until',
            fields.Date.today()
        )
        if timespan == 'week':
            timespan_until += relativedelta(weekday=SU)
        elif timespan == 'month':
            timespan_until += relativedelta(months=1, day=1, days=-1)
        return timespan_until

    @api.multi
    @api.depends('timespan_since', 'timespan_until')
    def _compute_name(self):
        for plan in self:
            plan.name = 'some name'
            # if plan.timespan

            # period_start = plan.timespan_since.strftime(
            #     '%V, %Y'
            # )
            # period_end = plan.timespan_until.strftime(
            #     '%V, %Y'
            # )

            # if period_start == period_end:
            #     plan.name = '%s %s' % (
            #         _('Week'),
            #         period_start,
            #     )
            # else:
            #     plan.name = '%s %s - %s' % (
            #         _('Weeks'),
            #         period_start,
            #         period_end,
            #     )
