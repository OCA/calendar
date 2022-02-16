# Copyright 2022 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from uuid import uuid4

from odoo import fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    uuid = fields.Char(readonly=True, default=lambda self: str(uuid4()))
