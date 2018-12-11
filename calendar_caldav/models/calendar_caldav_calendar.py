# Copyright 2018 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CalendarCaldavCalendar(models.Model):
    _name = 'calendar.caldav.calendar'

    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        required=True
    )

    caldav_id = fields.Char()

    caldav_name = fields.Char(
        string='Name'
    )

    sync = fields.Boolean(
        string='Synchronize',
        default=False
    )
