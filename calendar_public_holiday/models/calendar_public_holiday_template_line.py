# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from dateutil import easter

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CalendarPublicHolidayTemplateLine(models.Model):
    _name = "calendar.public.holiday.template.line"
    _description = "Calendar Public Holiday Template Line"
    _order = "date_type, date, day_offset, name"

    template_id = fields.Many2one(
        "calendar.public.holiday.template",
        "Template",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(required=True, translate=True)
    date_type = fields.Selection(
        [("fixed", "Fixed Date"), ("easter", "Easter Sunday")],
        required=True,
        default="fixed",
        help="Fixed Date: the day and month of the date are used every year.\n"
        "Other values: the date is calculated for every year.",
    )
    date = fields.Date(help="The year is ignored.")
    day_offset = fields.Integer(
        help="Number of days added to (or subtracted from, when negative) "
        "the calculated date."
    )
    state_ids = fields.Many2many(
        "res.country.state",
        "calendar_public_holiday_template_line_state_rel",
        "template_line_id",
        "state_id",
        "Related States",
    )

    @api.constrains("date_type", "date")
    def _check_date(self):
        for line in self:
            if line.date_type != "fixed":
                continue
            if not line.date:
                raise ValidationError(
                    self.env._(
                        "A date is required for the fixed holiday %s.", line.name
                    )
                )
            if line.date.month == 2 and line.date.day == 29:
                raise ValidationError(
                    self.env._(
                        "The 29th of February cannot be used as fixed holiday (%s).",
                        line.name,
                    )
                )

    def _get_date(self, year):
        self.ensure_one()
        date = getattr(self, f"_get_date_{self.date_type}")(year)
        return date + timedelta(days=self.day_offset)

    def _get_date_fixed(self, year):
        return self.date.replace(year=year)

    def _get_date_easter(self, year):
        return easter.easter(year)

    def _prepare_public_holiday_line_vals(self, public_holiday):
        self.ensure_one()
        return {
            "name": self.name,
            "date": self._get_date(public_holiday.year),
            "variable_date": self.date_type != "fixed",
            "state_ids": [(6, 0, self.state_ids.ids)],
            "public_holiday_id": public_holiday.id,
        }
