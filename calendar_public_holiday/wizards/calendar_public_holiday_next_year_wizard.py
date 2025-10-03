# Copyright 2016 Trobz
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CalendarPublicHolidayNextYear(models.TransientModel):
    _name = "calendar.public.holiday.next.year"
    _description = "Create Public Holiday From Existing Ones"

    public_holiday_ids = fields.Many2many(
        comodel_name="calendar.public.holiday",
        string="Templates",
        help="Select the public holidays to use as template. "
        "If not set, latest public holidays of each country will be used. "
        "Only the last templates of each country for each year will "
        "be taken into account (If you select templates from 2012 and 2015, "
        "only the templates from 2015 will be taken into account.",
    )
    year = fields.Integer(
        help="Year for which you want to create the public holidays. "
        "By default, the year following the template."
    )

    def create_public_holidays(self):
        self.ensure_one()
        last_ph_dict = {}
        ph_env = self.env["calendar.public.holiday"]
        pholidays = self.public_holiday_ids or ph_env.search([])
        if not pholidays:
            raise UserError(
                self.env._(
                    "No Public Holidays found as template. "
                    "Please create the first Public Holidays manually."
                )
            )
        for ph in pholidays:
            last_ph_country = last_ph_dict.get(ph.country_id, False)
            if last_ph_country:
                if last_ph_country.year < ph.year:
                    last_ph_dict[ph.country_id] = ph
            else:
                last_ph_dict[ph.country_id] = ph
        new_ph_ids = []
        for last_ph in last_ph_dict.values():
            new_year = self.year or last_ph.year + 1
            new_ph_vals = {"year": new_year}
            new_ph = last_ph.copy(new_ph_vals)
            new_ph_ids.append(new_ph.id)
            for last_ph_line in last_ph.line_ids:
                feb_29 = last_ph_line.date.month == 2 and last_ph_line.date.day == 29
                if feb_29:
                    # Handling this rare case would mean quite a lot of
                    # complexity because previous or next day might also be a
                    # public holiday.
                    raise UserError(
                        self.env._(
                            "You cannot use as template the public holidays "
                            "of a year that "
                            "includes public holidays on 29th of February "
                            "(2016, 2020...), please select a template from "
                            "another year."
                        )
                    )
                new_date = last_ph_line.date.replace(year=new_year)
                new_ph_line_vals = {"date": new_date, "public_holiday_id": new_ph.id}
                last_ph_line.copy(new_ph_line_vals)
        domain = [["id", "in", new_ph_ids]]
        action = {
            "type": "ir.actions.act_window",
            "name": self.env._("New public holidays"),
            "view_mode": "list,form",
            "res_model": ph_env._name,
            "domain": domain,
        }
        return action
