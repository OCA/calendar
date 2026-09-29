# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _matches_public_holiday_line(self, line):
        """Whether a nationwide ``line`` applies to this company.

        Nationwide public holidays are generated once per company, without a
        working schedule, which standard applies to every schedule of the
        company. An unknown company country cannot rule the holiday out --
        refusing it there would silently generate nothing at all, which is the
        far worse failure; ``_public_holiday_sync_issues`` reports it instead
        so the country can be filled in.
        """
        self.ensure_one()
        holiday_country = line.public_holiday_id.country_id
        if not holiday_country:
            return True
        return not self.country_id or holiday_country == self.country_id

    @api.model_create_multi
    def create(self, vals_list):
        # A shared working schedule (no company) carries the public holidays
        # of every company, so a new company needs its mirrors right away, not
        # at the next nightly synchronisation.
        companies = super().create(vals_list)
        if not self.env.context.get("public_holiday_sync"):
            self.env[
                "calendar.public.holiday.line"
            ]._get_lines_to_sync()._sync_global_leaves()
        return companies

    def write(self, vals):
        res = super().write(vals)
        if "country_id" in vals and not self.env.context.get("public_holiday_sync"):
            self.env[
                "calendar.public.holiday.line"
            ]._get_lines_to_sync()._sync_global_leaves()
        return res
