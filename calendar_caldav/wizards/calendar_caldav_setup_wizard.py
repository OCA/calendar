# Copyright 2018 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CalendarCaldavSetupWizard(models.TransientModel):
    _name = 'calendar.caldav.setup.wizard'

    user_id = fields.Many2one(
        comodel_name='res.users',
        required=True,
        default=lambda self: self.env.user.id
    )

    url = fields.Char(
        default=lambda self: self.env.user.caldav_url,
        required=True
    )

    username = fields.Char(
        default=lambda self: self.env.user.caldav_username,
        required=True
    )

    password = fields.Char(
        default=lambda self: self.env.user.caldav_password,
        required=True
    )

    @api.multi
    def confirm(self):
        self.ensure_one()
        self.user_id.sudo().write({
            'caldav_url': self.url,
            'caldav_username': self.username,
            'caldav_password': self.password
        })

        self.env['calendar.caldav'].sync_calendars(self.user_id)
        action = self.env.ref(
            'calendar_caldav.calendar_caldav_select_wizard_action').read()[0]
        action['default_user_id'] = self.user_id.id
        return action
