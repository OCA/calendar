# Copyright (C) 2020, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    calendar_event_id = fields.Many2one("calendar.event", "Calendar Event")

    def write(self, vals):
        res = super().write(vals)
        if self.calendar_event_id:
            if self.planned_date_begin != self.calendar_event_id.start:
                self.calendar_event_id.start = self.planned_date_begin
            if self.planned_date_end != self.calendar_event_id.stop:
                self.calendar_event_id.stop = self.planned_date_end
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if vals.get("planned_date_begin") and vals.get("planned_date_end"):
            event = self.env["calendar.event"].create(self.get_calendar_event_vals(res))
            event.project_task_id = res.id
            res.calendar_event_id = event.id
        return res

    def unlink(self):
        event_id = False
        if self.calendar_event_id:
            event_id = self.calendar_event_id.id
        res = super().unlink()
        if event_id:
            self.env["calendar.event"].browse(event_id).unlink()
        return res

    def get_calendar_event_vals(self, project_task):
        return {
            "name": project_task.name,
            "start": project_task.planned_date_begin,
            "stop": project_task.planned_date_end,
        }
