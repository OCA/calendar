# Copyright 2018 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    caldav_id = fields.Char(
        string='Caldav UID'
    )

    caldav_odoo_last_update = fields.Datetime()

    caldav_last_update = fields.Datetime()

    @api.multi
    def write(self, vals):
        if 'caldav_id' not in vals:
            vals['caldav_odoo_last_update'] = fields.Datetime.now()
        return super(CalendarEvent, self).write(vals)

    @api.multi
    def unlink(self):
        if 'remove_sync' not in self.env.context or \
                not self.env.context['remove_sync']:
            for cal in self:
                if cal.caldav_id:
                    raise UserError(
                        _('Please delete CalDAV events from your CalDAV calendar.')
                    )

        return super(CalendarEvent, self).unlink()
