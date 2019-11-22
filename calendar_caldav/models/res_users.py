# Copyright 2018 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    caldav_url = fields.Char(
        string='CalDAV Url'
    )

    caldav_username = fields.Char(
        string='CalDAV Username'
    )

    caldav_password = fields.Char(
        string='CalDAV Password'
    )

    caldav_calendar_ids = fields.One2many(
        comodel_name='calendar.caldav.calendar',
        inverse_name='user_id',
        string='Select Calendars'
    )

    def __init__(self, pool, cr):
        super(ResUsers, self).__init__(pool, cr)

        caldav_fields = [
            'caldav_url',
            'caldav_username',
            'caldav_password',
            'caldav_calendar_ids'
        ]

        self.SELF_READABLE_FIELDS += caldav_fields
        self.SELF_WRITEABLE_FIELDS += caldav_fields

    @api.multi
    def sync_caldav_calendars(self):
        self.ensure_one()
        self.env['calendar.caldav'].sync_calendars(self)
        return {
            "type": "ir.actions.do_nothing",
        }

    @api.multi
    def remove_caldav_sync(self):
        self.ensure_one()
        self.caldav_url = False
        self.caldav_username = False
        self.caldav_password = False
        self.caldav_calendar_ids.unlink()
        self.env['calendar.event'].with_context({'remove_sync': True}).search([
            ('user_id', '=', self.id),
            ('caldav_id', '!=', False)
        ]).unlink()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload_context',
        }

