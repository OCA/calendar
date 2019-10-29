# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProjectTask(models.Model):
    _name = "project.task"
    _inherit = ["project.task", "calendar.event.link.mixin"]
