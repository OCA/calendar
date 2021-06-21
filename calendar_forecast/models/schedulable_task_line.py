# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# Copyright 2018-2019 Brainbean Apps (https://brainbeanapps.com)
# Copyright 2020 César López Ramírez <cesar.lopez@coopdevs.org>
# Copyright 2021 Iván García <kapis@riseup.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CalendarSchedulable(models.AbstractModel):
    _name = "calendar.schedulable.abstract"
    employee_domain_ids = fields.Many2many(
        compute="_compute_employee_domain_ids",
        comodel_name="hr.employee",
        string="Available Employees",
    )
    employee_scheduling_ids = fields.Many2many(
        compute="_compute_employee_scheduling_ids",
        comodel_name="hr.employee",
        string="Employees Scheduling",
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Assigned to employee",
        domain="[('id', 'in', employee_domain_ids)]",
        help="If the task is not scheduled (without ending date), the "
        "automated scheduling will only assign the task to the employee "
        "selected here.",
    )
    employee_category_id = fields.Many2one(
        comodel_name="hr.employee.category",
        string="Employee category",
        help="Only employee selected on the project belonging to the task "
        "that have the categories selected here can do the task.",
    )
    employee_ids = fields.Many2many(
        comodel_name="hr.employee",
        string="Employees",
    )
    employee_or_category = fields.Char(
        compute="_compute_employee_or_category",
        context_dependent=True,
    )

    date = fields.Date(
        string="Date",
        required=True,
        index=True,
    )

    unit_amount = fields.Float(
        string="Quantity",
        default=0.0,
    )

    @api.multi
    @api.depends("employee_ids.category_ids", "employee_category_id")
    def _compute_employee_domain_ids(self):
        for record in self:
            emp = record.mapped("employee_ids")
            task_skill = record.employee_category_id
            if task_skill:
                emp = emp.filtered(lambda r: task_skill in r.category_ids)
            record.employee_domain_ids = emp.ids

    @api.multi
    @api.depends("task_id.date_end", "employee_id", "employee_domain_ids")
    def _compute_employee_scheduling_ids(self):
        for record in self:
            employees = record.employee_id
            if record.task_id.date_end or not record.employee_id:
                employees = record.employee_domain_ids
            record.employee_scheduling_ids = employees

    @api.multi
    @api.depends("employee_id", "employee_category_id")
    def _compute_employee_or_category(self):
        for record in self:
            if record.employee_id:
                record.employee_or_category = record.employee_id.name_get()[0][1]
            elif record.employee_category_id:
                record.employee_or_category = record.employee_category_id.name_get()[0][1]
            else:
                record.employee_or_category = ""

    @api.onchange("employee_domain_ids")
    def _onchange_employee_domain_ids(self):
        if self.employee_id not in self.employee_domain_ids:
            self.employee_id = False


class SchedulableTaskLine(models.Model):
    _inherit = ["calendar.schedulable.abstract"]
    _name = "calendar.schedulable.task.line"
    _rec_name = "task_id"

    forecast_id = fields.Many2one(
        comodel_name="calendar.forecast",
        string="Sheet",
    )

    task_id = fields.Many2one(
        comodel_name="project.task",
        string="Task",
    )

    period = fields.Char(
        compute="_compute_period",
        context_dependent=True,
    )

    name = fields.Char(
        compute="_compute_name",
        context_dependent=True,
    )

    @api.depends("task_id.name", "employee_id", "employee_category_id")
    def _compute_name(self):
        for sheet in self:
            if sheet.employee_id:
                name = "%s - Empl: %s" % (
                    sheet.task_id.name_get()[0][1],
                    sheet.employee_id.name_get()[0][1],
                )
            elif sheet.employee_category_id:
                return "%s - Cat: %s" % (
                    sheet.task_id.name_get()[0][1],
                    sheet.employee_category_id.name_get()[0][1],
                )
            else:
                name = sheet.task_id.name_get()[0][1]
            sheet.name = name

    @api.multi
    @api.depends("task_id.date_start", "task_id.date_end")
    def _compute_period(self):
        for record in self:
            record.period = _("Period <%s - %s>") % (
                record.forecast_id.date_start,
                record.forecast_id.date_end,
            )

    @api.multi
    def _get_sheet_domain(self):
        """ Hook for extensions """
        self.ensure_one()
        return [
            ("company_id", "in", [self.task_id.company_id.id, False]),
        ]

    @api.multi
    def _determine_sheet(self):
        """ Hook for extensions """
        self.ensure_one()
        return self.env["calendar.forecast"].search(
            self._get_sheet_domain(),
            limit=1,
        )

    def _compute_sheet(self):
        """Links the timesheet line to the corresponding sheet"""
        for timesheet in self.filtered("task_id"):
            sheet = timesheet._determine_sheet()
            if timesheet.forecast_id != sheet:
                timesheet.forecast_id = sheet

    @api.multi
    @api.constrains("task_id", "forecast_id")
    def _check_company_id_forecast_id(self):
        for aal in self.sudo():
            if (
                aal.task_id.company_id
                and aal.forecast_id.company_id
                and aal.task_id.company_id != aal.forecast_id.company_id
            ):
                raise ValidationError(
                    _(
                        "You cannot create a timesheet of a different company "
                        "than the one of the timesheet sheet:"
                        "\n - %s of %s"
                        "\n - %s of %s"
                        % (
                            aal.forecast_id.complete_name,
                            aal.forecast_id.company_id.name,
                            aal.task_id.name,
                            aal.task_id.company_id.name,
                        )
                    )
                )

    @api.model
    def create(self, values):

        if not self.env.context.get("sheet_create") and "forecast_id" in values:
            del values["forecast_id"]
        if "date" not in values:
            forecast = self.env["calendar.forecast"].search(
                [("id", "in", [values["forecast_id"]])]
            )
            values["date"] = forecast.date_start
        res = super().create(values)
        res._compute_sheet()
        return res

    @api.model
    def _sheet_create(self, values):
        return self.with_context(sheet_create=True).create(values)

    @api.multi
    def write(self, values):

        res = super().write(values)
        if self._timesheet_should_compute_sheet(values):
            self._compute_sheet()
        return res

    @api.model
    def _timesheet_should_check_write(self, values):
        """ Hook for extensions """
        return bool(set(self._get_timesheet_protected_fields()) & set(values.keys()))

    @api.model
    def _timesheet_should_compute_sheet(self, values):
        """ Hook for extensions """
        return any(f in self._get_sheet_affecting_fields() for f in values)

    @api.model
    def _get_timesheet_protected_fields(self):
        """ Hook for extensions """
        return [
            "name",
            "date",
            "unit_amount",
            "user_id",
            "employee_id",
            "company_id",
            "task_id",
            "project_id",
            "forecast_id",
        ]

    @api.model
    def _get_sheet_affecting_fields(self):
        """ Hook for extensions """
        return ["date", "employee_id", "project_id", "company_id"]

    @api.multi
    def merge_timesheets(self):

        unit_amount = sum([t.unit_amount for t in self])
        self[0].write(
            {
                "unit_amount": unit_amount,
            }
        )
        self[1:].unlink()
        return self[0]
