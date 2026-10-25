# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CalendarPublicHolidayTemplate(models.Model):
    _name = "calendar.public.holiday.template"
    _description = "Calendar Public Holiday Template"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    country_id = fields.Many2one("res.country", "Country")
    line_ids = fields.One2many(
        "calendar.public.holiday.template.line",
        "template_id",
        "Holidays",
    )
    generate_year = fields.Integer(
        "Year",
        default=lambda self: fields.Date.context_today(self).year,
        copy=False,
        help="Year for which the public holidays are generated.",
    )

    def _prepare_public_holiday_line_vals(self, public_holiday):
        self.ensure_one()
        return [
            line._prepare_public_holiday_line_vals(public_holiday)
            for line in self.line_ids
        ]

    def create_public_holidays(self, year):
        """Create the public holidays of this template for the given year.

        Existing holidays of the same year and country are replaced.
        :param year: year as integer
        :return: calendar.public.holiday record
        """
        self.ensure_one()
        public_holiday_model = self.env["calendar.public.holiday"]
        public_holiday = public_holiday_model.search(
            [("year", "=", year), ("country_id", "=", self.country_id.id)], limit=1
        )
        if public_holiday:
            public_holiday.line_ids.unlink()
        else:
            public_holiday = public_holiday_model.create(
                {"year": year, "country_id": self.country_id.id}
            )
        self.env["calendar.public.holiday.line"].create(
            self._prepare_public_holiday_line_vals(public_holiday)
        )
        return public_holiday

    def action_generate_public_holidays(self):
        self.ensure_one()
        public_holiday = self.create_public_holidays(self.generate_year)
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Public Holidays"),
            "res_model": public_holiday._name,
            "res_id": public_holiday.id,
            "view_mode": "form",
        }
