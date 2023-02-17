# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from .resource_booking import _availability_is_fitting


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    @api.constrains("calendar_id", "resource_type", "tz", "user_id")
    def _check_bookings_scheduling(self):
        """Scheduled bookings must have no conflicts."""
        bookings = self.env["resource.booking"].search(
            [("combination_id.resource_ids", "in", self.ids)]
        )
        return bookings._check_scheduling()

    def is_available(self, start_dt, end_dt, domain=None, tz=None):
        """Convenience method to check whether a resource is available within a
        time span.
        """
        self.ensure_one()
        # the `analyzing_booking` context needs to be added here, or bookings
        # are not marked as busy. Because we do not actually have a booking_id
        # available here, we set the value to -1.
        result = self.calendar_id.with_context(analyzing_booking=-1)._work_intervals(
            start_dt, end_dt, resource=self, domain=domain, tz=tz
        )
        return _availability_is_fitting(result, start_dt, end_dt)
