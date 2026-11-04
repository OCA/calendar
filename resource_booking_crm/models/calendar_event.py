# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    @api.model_create_multi
    def create(self, vals_list):
        events = super(
            CalendarEvent, self.with_context(resource_booking_crm_creating_event=True)
        ).create(vals_list)
        for event in events.sudo().filtered(
            lambda e: not e.opportunity_id and e.resource_booking_ids.lead_id
        ):
            event.opportunity_id = event.resource_booking_ids.lead_id[:1]
        return events.with_env(self.env)
