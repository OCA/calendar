# Copyright (C) 2020, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class Meeting(models.Model):
    _inherit = "calendar.event"

    fsm_order_id = fields.Many2one('fsm.order', 'FSM Order')

    def write(self, vals):
        res = super().write(vals)
        if self.fsm_order_id:
            if self.start != self.fsm_order_id.scheduled_date_start:
                self.fsm_order_id.scheduled_date_start = self.start
            if self.stop != self.fsm_order_id.scheduled_date_end:
                self.fsm_order_id.duration = self.duration
        return res

    def unlink(self):
        if self.fsm_order_id:
            self.fsm_order_id.\
                message_post(body=_("%s has deleted the calendar event \
                                associated wtih this FSM Order") %
                             self.env.user.name)
        return super().unlink()
