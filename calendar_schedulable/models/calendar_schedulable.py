from odoo import models, fields, api


class CalendarSchedulable(models.AbstractModel):
    _name = 'calendar.schedulable'
    employee_domain_ids = fields.Many2many(
        compute='_compute_employee_domain_ids',
        comodel_name='hr.employee',
        string="Available Employees",
    )
    employee_scheduling_ids = fields.Many2many(
        compute='_compute_employee_scheduling_ids',
        comodel_name='hr.employee',
        string="Employees Scheduling",
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Assigned to employee",
        domain="[('id', 'in', employee_domain_ids)]",
        help="If the task is not scheduled (without ending date), the "
             "automated scheduling will only assign the task to the employee "
             "selected here.",
    )
    employee_category_id = fields.Many2one(
        comodel_name='hr.employee.category',
        string="Employee category",
        help="Only employee selected on the project belonging to the task "
             "that have the categories selected here can do the task.",
    )
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string="Employees",
    )
    date_start = fields.Datetime(string='Starting Date',
                                 default=fields.Datetime.now,
                                 index=True, copy=False)
    date_end = fields.Datetime(string='Ending Date', index=True, copy=False)
    date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False, readonly=True)
    date_deadline = fields.Date(string='Deadline', index=True, copy=False)

    @api.multi
    @api.depends('employee_ids.category_ids',
                 'employee_category_id')
    def _compute_employee_domain_ids(self):
        for record in self:
            emp = record.mapped('employee_ids')
            task_skill = record.employee_category_id
            if task_skill:
                emp = emp.filtered(lambda r: task_skill in r.category_ids)
            record.employee_domain_ids = emp.ids

    @api.multi
    @api.depends('date_end', 'employee_id', 'employee_domain_ids')
    def _compute_employee_scheduling_ids(self):
        for record in self:
            employees = record.employee_id
            if record.date_end or not record.employee_id:
                employees = record.employee_domain_ids
            record.employee_scheduling_ids = employees

    @api.onchange('employee_domain_ids')
    def _onchange_employee_domain_ids(self):
        if self.employee_id not in self.employee_domain_ids:
            self.employee_id = False
