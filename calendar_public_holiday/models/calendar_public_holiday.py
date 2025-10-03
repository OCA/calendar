# Copyright 2015 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>
# Copyright 2020 InitOS Gmbh
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResourceCalendarPublicHoliday(models.Model):
    _name = "calendar.public.holiday"
    _description = "Calendar Public Holiday"
    _rec_name = "year"
    _order = "year desc"

    year = fields.Integer(
        "Calendar Year",
        required=True,
        default=lambda self: fields.Date.context_today(self).year,
    )
    line_ids = fields.One2many(
        "calendar.public.holiday.line",
        "public_holiday_id",
        "Holiday Dates",
    )
    country_id = fields.Many2one("res.country", "Country")

    @api.constrains("year", "country_id")
    def _check_year(self):
        for line in self:
            line._check_year_one()

    def _check_year_one(self):
        if self.search_count(
            [
                ("year", "=", self.year),
                ("country_id", "=", self.country_id.id),
                ("id", "!=", self.id),
            ]
        ):
            raise ValidationError(
                self.env._(
                    "You can't create duplicate public holiday per year and/or"
                    " country"
                )
            )
        return True

    @api.depends("country_id")
    def _compute_display_name(self):
        for line in self:
            if line.country_id:
                line.display_name = f"{line.year} ({line.country_id.name})"
            else:
                line.display_name = line.year

    def _get_domain_states_filter(self, pholidays, start_dt, end_dt, partner_id=None):
        partner = self.env["res.partner"].browse(partner_id)
        states_filter = [
            ("public_holiday_id", "in", pholidays.ids),
            ("date", ">=", start_dt),
            ("date", "<=", end_dt),
        ]
        if partner and partner.state_id:
            states_filter.extend(
                [
                    "|",
                    ("state_ids", "in", partner.state_id.ids),
                    ("state_ids", "=", False),
                ]
            )
        else:
            states_filter.append(("state_ids", "=", False))
        return states_filter

    @api.model
    @api.returns("calendar.public.holiday.line")
    def get_holidays_list(self, year=None, start_dt=None, end_dt=None, partner_id=None):
        """Returns recordset of calendar.public.holiday.line
        for the specified year and employee
        :param year: year as string (optional if start_dt and end_dt defined)
        :param start_dt: start_dt as date
        :param end_dt: end_dt as date
        :param partner_id: ID of the partner
        :return: recordset of calendar.public.holiday.line
        """
        partner = self.env["res.partner"].browse(partner_id)
        if not start_dt and not end_dt:
            start_dt = datetime.date(year, 1, 1)
            end_dt = datetime.date(year, 12, 31)
        years = list(range(start_dt.year, end_dt.year + 1))
        holidays_filter = [("year", "in", years)]
        if partner:
            if partner.country_id:
                holidays_filter.append(
                    ("country_id", "in", (False, partner.country_id.id))
                )
            else:
                holidays_filter.append(("country_id", "=", False))
        public_holidays = self.search(holidays_filter)
        public_holiday_line = self.env["calendar.public.holiday.line"]
        if not public_holidays:
            return public_holiday_line
        states_filter = self._get_domain_states_filter(
            public_holidays, start_dt, end_dt, partner_id=partner.id
        )
        return public_holiday_line.search(states_filter)

    @api.model
    def is_public_holiday(self, selected_date, partner_id=None):
        """
        Returns True if selected_date is a public holiday for the employee
        :param selected_date: datetime object
        :param partner_id: ID of the partner
        :return: bool
        """
        partner = self.env["res.partner"].browse(partner_id)
        partner_id = partner.id if partner else None
        holidays_lines = self.get_holidays_list(
            year=selected_date.year, partner_id=partner_id
        )
        if holidays_lines:
            hol_date = holidays_lines.filtered(lambda r: r.date == selected_date)
            if hol_date:
                return True
        return False
