# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from odoo.addons.resource.models.resource import Intervals


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    @api.model
    def _calendar_event_busy_intervals(
        self, start_dt, end_dt, resource, analyzed_booking_id
    ):
        if resource.resource_type == "user":
            return Intervals([])
        return super()._calendar_event_busy_intervals(
            start_dt, end_dt, resource, analyzed_booking_id
        )
