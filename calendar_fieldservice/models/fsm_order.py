# Copyright (C) 2020, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FSMOrder(models.Model):
    _inherit = "fsm.order"

    calendar_event_id = fields.Many2one("calendar.event", "Calendar Event")

    def write(self, vals):
        res = super().write(vals)
        if self.calendar_event_id:
            if self.scheduled_date_start != self.calendar_event_id.start:
                self.calendar_event_id.start = self.scheduled_date_start
            if self.scheduled_date_end != self.calendar_event_id.stop:
                self.calendar_event_id.stop = self.scheduled_date_end
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if vals.get("scheduled_date_start") and vals.get("scheduled_date_end"):
            event = self.env["calendar.event"].create(self.get_calendar_event_vals(res))
            event.fsm_order_id = res.id
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

    def get_calendar_event_vals(self, fsm_order):
        return {
            "name": fsm_order.name,
            "start": fsm_order.scheduled_date_start,
            "stop": fsm_order.scheduled_date_end,
        }
