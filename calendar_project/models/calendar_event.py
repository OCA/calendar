# Copyright (C) 2020, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class Meeting(models.Model):
    _inherit = "calendar.event"

    project_task_id = fields.Many2one("project.task", "Task")

    def write(self, vals):
        res = super().write(vals)
        if self.project_task_id:
            if self.start != self.project_task_id.planned_date_begin:
                self.project_task_id.planned_date_begin = self.start
            if self.stop != self.project_task_id.planned_date_end:
                self.project_task_id.planned_date_end = self.stop
        return res

    def unlink(self):
        if self.project_task_id:
            self.project_task_id.message_post(
                body=_(
                    "%s has deleted the calendar event \
                                associated wtih this Task"
                )
                % self.env.user.name
            )
        return super().unlink()
