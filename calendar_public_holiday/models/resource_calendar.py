# Copyright 2026 XtremXpert
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _public_holiday_timezone(self):
        """Timezone used to bound a public holiday on this calendar.

        Odoo 20 removed ``tz`` from ``resource.calendar``: the timezone now
        lives on the resource (or, failing that, on the company). Use the first
        resource working from this calendar, as the booking engines do.
        """
        self.ensure_one()
        resource = self.env["resource.resource"].search(
            [("calendar_id", "=", self.id)], limit=1
        )
        return resource.tz or self.company_id.partner_id.tz or "UTC"
