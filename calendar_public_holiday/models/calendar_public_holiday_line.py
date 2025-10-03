# Copyright 2015 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>
# Copyright 2020 InitOS Gmbh
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api, fields, models
from odoo.exceptions import ValidationError


class CalendarHolidaysPublicLine(models.Model):
    _name = "calendar.public.holiday.line"
    _description = "Calendar Public Holiday Line"
    _order = "date, name desc"

    name = fields.Char(required=True)
    date = fields.Date(required=True)
    public_holiday_id = fields.Many2one(
        "calendar.public.holiday",
        "Calendar Year",
        required=True,
        ondelete="cascade",
    )
    variable_date = fields.Boolean("Date may change", default=True)
    state_ids = fields.Many2many(
        "res.country.state",
        "public_holiday_state_rel",
        "public_holiday_line_id",
        "state_id",
        "Related States",
    )
    meeting_id = fields.Many2one(
        "calendar.event",
        string="Meeting",
        copy=False,
    )

    @api.constrains("date", "state_ids")
    def _check_date_state(self):
        for line in self:
            line._check_date_state_one()

    def _get_domain_check_date_state_one_state_ids(self):
        return [
            ("date", "=", self.date),
            ("public_holiday_id", "=", self.public_holiday_id.id),
            ("state_ids", "!=", False),
            ("id", "!=", self.id),
        ]

    def _get_domain_check_date_state_one(self):
        return [
            ("date", "=", self.date),
            ("public_holiday_id", "=", self.public_holiday_id.id),
            ("state_ids", "=", False),
        ]

    def _check_date_state_one(self):
        if self.date.year != self.public_holiday_id.year:
            raise ValidationError(
                self.env._(
                    "Dates of holidays should be the same year as the calendar"
                    " year they are being assigned to"
                )
            )
        if self.state_ids:
            domain = self._get_domain_check_date_state_one_state_ids()
            holidays = self.search(domain)
            for holiday in holidays:
                if self.state_ids & holiday.state_ids:
                    raise ValidationError(
                        self.env._(
                            "You can't create duplicate public holiday per date"
                            f" {self.date} and one of the country states."
                        )
                    )
        domain = self._get_domain_check_date_state_one()
        if self.search_count(domain) > 1:
            raise ValidationError(
                self.env._(
                    f"You can't create duplicate public holiday per date {self.date}."
                )
            )
        return True

    def _prepare_holidays_meeting_values(self):
        self.ensure_one()
        categ_id = self.env.ref("calendar_public_holiday.event_type_holiday", False)
        meeting_values = {
            "name": (
                f"{self.name} ({self.public_holiday_id.country_id.name})"
                if self.public_holiday_id.country_id
                else self.name
            ),
            "description": ", ".join(self.state_ids.mapped("name")),
            "start": self.date,
            "stop": self.date,
            "allday": True,
            "user_id": SUPERUSER_ID,
            "privacy": "confidential",
            "show_as": "busy",
        }
        if categ_id:
            meeting_values.update({"categ_ids": [(6, 0, categ_id.ids)]})
        return meeting_values

    @api.constrains("date", "name", "public_holiday_id", "state_ids")
    def _update_calendar_event(self):
        for rec in self:
            if rec.meeting_id:
                rec.meeting_id.write(rec._prepare_holidays_meeting_values())

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            record.meeting_id = self.env["calendar.event"].create(
                record._prepare_holidays_meeting_values()
            )
        return res

    def unlink(self):
        self.mapped("meeting_id").unlink()
        return super().unlink()
