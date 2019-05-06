# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo import fields
from odoo.tests import common


class TestResourcePlanning(common.TransactionCase):

    def setUp(self):
        super().setUp()

        self.today = fields.Date.today()
        self.ResourceAllocationPlan = self.env['resource.allocation.plan']
        self.ResourceAllocationLine = self.env['resource.allocation.line']

    def test_default_timespan_since_day(self):
        self.env.user.company_id.resource_planning_timespan = 'day'
        plan_1 = self.ResourceAllocationPlan.with_context({
            'default_timespan_since': date(2019, 4, 1)
        }).create()
        self.assertEqual(plan_1.timespan_since, date(2019, 4, 1))

        plan_2 = self.ResourceAllocationPlan.with_context({
            'default_timespan_since': date(2019, 4, 2)
        }).create()
        self.assertEqual(plan_2.timespan_since, date(2019, 4, 2))

    def test_default_timespan_since_week(self):
        self.env.user.company_id.resource_planning_timespan = 'week'
        plan_1 = self.ResourceAllocationPlan.with_context({
            'default_timespan_since': date(2019, 4, 1)
        }).create()
        self.assertEqual(plan_1.timespan_since, date(2019, 4, 1))

        plan_2 = self.ResourceAllocationPlan.with_context({
            'default_timespan_since': date(2019, 4, 2)
        }).create()
        self.assertEqual(plan_2.timespan_since, date(2019, 4, 1))

    def test_default_timespan_since_month(self):
        self.env.user.company_id.resource_planning_timespan = 'month'
        plan_1 = self.ResourceAllocationPlan.with_context({
            'default_timespan_since': date(2019, 4, 1)
        }).create()
        self.assertEqual(plan_1.timespan_since, date(2019, 4, 1))

        plan_2 = self.ResourceAllocationPlan.with_context({
            'default_timespan_since': date(2019, 4, 2)
        }).create()
        self.assertEqual(plan_2.timespan_since, date(2019, 4, 1))

    def test_default_timespan_until_day(self):
        self.env.user.company_id.resource_planning_timespan = 'day'
        plan_1 = self.ResourceAllocationPlan.with_context({
            'default_timespan_until': date(2019, 4, 6)
        }).create()
        self.assertEqual(plan_1.timespan_until, date(2019, 4, 1))

        plan_2 = self.ResourceAllocationPlan.with_context({
            'default_timespan_until': date(2019, 4, 6)
        }).create()
        self.assertEqual(plan_2.timespan_until, date(2019, 4, 6))

    def test_default_timespan_until_week(self):
        self.env.user.company_id.resource_planning_timespan = 'week'
        plan_1 = self.ResourceAllocationPlan.with_context({
            'default_timespan_until': date(2019, 4, 1)
        }).create()
        self.assertEqual(plan_1.timespan_until, date(2019, 4, 6))

        plan_2 = self.ResourceAllocationPlan.with_context({
            'default_timespan_until': date(2019, 4, 6)
        }).create()
        self.assertEqual(plan_2.timespan_until, date(2019, 4, 6))

    def test_default_timespan_until_month(self):
        self.env.user.company_id.resource_planning_timespan = 'month'
        plan_1 = self.ResourceAllocationPlan.with_context({
            'default_timespan_until': date(2019, 4, 1)
        }).create()
        self.assertEqual(plan_1.timespan_until, date(2019, 4, 30))

        plan_2 = self.ResourceAllocationPlan.with_context({
            'default_timespan_until': date(2019, 4, 30)
        }).create()
        self.assertEqual(plan_2.timespan_until, date(2019, 4, 30))
