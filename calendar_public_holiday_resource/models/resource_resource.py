# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    def unlink(self):
        # `resource.calendar.leaves.resource_id` is nullified when its
        # resource goes (default ondelete), which would promote a personal
        # public holiday mirror to a schedule-wide one -- and a second
        # nullified mirror of the same line, schedule and company would then
        # violate the unique index and abort the deletion. Deleting an
        # employee deletes its resource, so the mirrors go first, through the
        # ORM to keep leave re-evaluation and timesheet cleanup running.
        mirrors = (
            self.env["resource.calendar.leaves"]
            .sudo()
            .search(
                [
                    ("public_holiday_line_id", "!=", False),
                    ("resource_id", "in", self.ids),
                ]
            )
        )
        if mirrors:
            line_model = self.env["calendar.public.holiday.line"]
            mirrors = line_model._with_public_holiday_companies(
                mirrors.with_context(**line_model._sync_leave_context())
            )
            mirrors.unlink()
        return super().unlink()
