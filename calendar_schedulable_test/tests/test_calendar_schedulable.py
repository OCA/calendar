from odoo.tests.common import TransactionCase


class CalendarSchedulableTest(TransactionCase):

    def setUp(self):
        super(CalendarSchedulableTest, self).setUp()

        self.partner_1 = self.env['res.partner'].create({
            'name': 'partner 1',
            'employee_ids': [
                (6, 0, [self.ref('hr.employee_jth'), self.ref('hr.employee_admin')])
            ],
            'employee_category_id': self.ref('hr.employee_category_5')
        })
        self.partner_2 = self.env['res.partner'].create({
            'name': 'partner 2',
            'employee_ids': [
                (6, 0, [self.ref('hr.employee_jth'), self.ref('hr.employee_admin')])
            ]
        })
        self.partner_3 = self.env['res.partner'].create({
            'name': 'partner 3',
            'employee_ids': [
                (6, 0, [self.ref('hr.employee_jth'), self.ref('hr.employee_admin')])
            ]
        })
        self.partner_7 = self.env['res.partner'].create({
            'name': 'partner 7',
            'employee_ids': [
                (6, 0, [self.ref('hr.employee_jth'), self.ref('hr.employee_admin')])
            ],
            'employee_category_id': self.ref('hr.employee_category_3')
        })

    def test_employee_domain_ids(self):
        jth = self.browse_ref('hr.employee_jth')
        admin = self.browse_ref('hr.employee_admin')
        self.assertEquals(self.partner_3.employee_domain_ids, jth+admin)
        self.assertEquals(self.partner_2.employee_domain_ids, jth+admin)
        self.assertEquals(self.partner_7.employee_domain_ids, admin)
        self.assertEquals(self.partner_1.employee_domain_ids, jth)
