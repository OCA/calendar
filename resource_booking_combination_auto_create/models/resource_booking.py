# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models


class ResourceBooking(models.Model):
    _inherit = "resource.booking"
    # override constraint to allow to save resource bookings without
    # combinations in pending state.
    _sql_constraints = [
        (
            "combination_required_if_event",
            "check(meeting_id is null or state = 'pending' or combination_id is not null)",
            "Missing resource booking combination.",
        ),
    ]

    # change default value
    combination_auto_assign = fields.Boolean(default=False)

    def _check_scheduling(self):
        has_meeting = self.filtered("meeting_id")
        if not has_meeting:
            return
        has_rbc = self.filtered("combination_id.resource_ids")
        ready_rbc = has_meeting & has_rbc
        # only check scheduling for bookings that have a meeting and a
        # combination.
        return super(ResourceBooking, ready_rbc)._check_scheduling()

    def _compute_state(self):
        for rb in self:
            super(ResourceBooking, rb)._compute_state()
            if rb.state == "scheduled" and not rb.combination_id:
                # stay in pending state when a start date is set but no
                # combination.
                rb.state = "pending"
