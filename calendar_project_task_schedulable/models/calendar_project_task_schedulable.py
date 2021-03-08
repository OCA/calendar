from odoo import models, fields, api


class CalendarProjectTaskSchedulable(models.Model):
    _name = "calendar.project.task.schedulable"
    _description = "Project Task Schedulable"
    _inherit = ["project.task", "calendar.schedulable"]


class CalendarProjectSchedule(models.Model):
    _name = "calendar.project.schedule"
    _description = "Project Forecasted Schedule"
    _inherit = "project.project"

    scheduled_tasks = fields.One2many(
        "project.task", "project_id", string="Tasks Scheduled"
    )
