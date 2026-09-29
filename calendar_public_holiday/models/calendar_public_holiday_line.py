# Copyright 2015 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>
# Copyright 2020 InitOS Gmbh
# Copyright 2024 Camptocamp
# Copyright 2026 glueckkanja AG
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
    region_ids = fields.Many2many(
        "calendar.public.holiday.region",
        "calendar_public_holiday_line_region_rel",
        "line_id",
        "region_id",
        string="Regions",
        help="The regions this public holiday is observed at. Leave empty "
        "for a nationwide public holiday.",
    )
    active = fields.Boolean(
        default=True,
        help="A disabled public holiday is ignored everywhere but keeps its "
        "configuration. Use this to switch off a public holiday whose "
        "regions are gone -- a line whose regions no longer exist "
        "would otherwise fall back to applying to everybody.",
    )
    meeting_id = fields.Many2one(
        "calendar.event",
        string="Meeting",
        copy=False,
    )

    @api.depends("name", "public_holiday_id.year", "public_holiday_id.country_id")
    def _compute_display_name(self):
        """Tell the same public holiday of different years apart.

        The plain name repeats every year, so any reference to a line could
        not say which year's holiday it meant. The year and the country are
        read one by one rather than through the calendar's own display name,
        which is already parenthesised and would nest.
        """
        for record in self:
            holiday = record.public_holiday_id
            if not holiday.year:
                record.display_name = record.name
                continue
            country = holiday.country_id.name
            scope = f"{holiday.year} - {country}" if country else str(holiday.year)
            record.display_name = f"{record.name} ({scope})"

    def _has_public_holiday_scope(self):
        """Whether this line is scoped rather than nationwide.

        A nationwide line applies to everybody of the country; a scoped one
        only to the people of the regions it names. Extension point: other
        modules add their own scoping dimensions on top.
        """
        self.ensure_one()
        return bool(self.region_ids)

    @api.constrains("date", "region_ids")
    def _check_date_region(self):
        for line in self:
            line._check_date_region_one()

    def _get_domain_check_date_region_one_region_ids(self):
        return [
            ("date", "=", self.date),
            ("public_holiday_id", "=", self.public_holiday_id.id),
            ("region_ids", "!=", False),
            ("id", "!=", self.id),
        ]

    def _get_domain_check_date_region_one(self):
        return [
            ("date", "=", self.date),
            ("public_holiday_id", "=", self.public_holiday_id.id),
            ("region_ids", "=", False),
        ]

    def _check_date_region_one(self):
        if self.date.year != self.public_holiday_id.year:
            raise ValidationError(
                self.env._(
                    "Dates of holidays should be the same year as the calendar"
                    " year they are being assigned to"
                )
            )
        if self.region_ids:
            domain = self._get_domain_check_date_region_one_region_ids()
            holidays = self.search(domain)
            for holiday in holidays:
                if self.region_ids & holiday.region_ids:
                    raise ValidationError(
                        self.env._(
                            "You can't create duplicate public holiday per date %s "
                            "and one of the regions.",
                            self.date,
                        )
                    )
        domain = self._get_domain_check_date_region_one()
        if self.search_count(domain) > 1:
            raise ValidationError(
                self.env._(
                    "You can't create duplicate public holiday per date %s.",
                    self.date,
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
            "description": ", ".join(self.region_ids.mapped("name")),
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

    @api.constrains("date", "name", "public_holiday_id", "region_ids")
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
