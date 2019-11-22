# Copyright 2018 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta
from odoo import api, fields, models


class CalendarCaldavSelectWizard(models.TransientModel):
    _name = 'calendar.caldav.select.wizard'

    user_id = fields.Many2one(
        comodel_name='res.users',
        required=True,
        default=lambda self: self.env.user.id
    )

    user_caldav_calendar_ids = fields.One2many(
        related='user_id.caldav_calendar_ids'
    )

    @api.multi
    def confirm(self):
        self.ensure_one()

        now = datetime.now()
        start = now - timedelta(days=365)
        end = now + timedelta(days=365)

        self.env['calendar.caldav'].sync_events(
            self.user_id,
            fields.Datetime.to_string(start),
            fields.Datetime.to_string(end)
        )
        return self.env.ref('calendar.action_calendar_event').read()[0]
