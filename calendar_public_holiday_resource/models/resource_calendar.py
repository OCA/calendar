# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

SYNC_TRIGGER_FIELDS = {
    "public_holiday_employee_sync",
    "company_id",
    "tz",
    "active",
}


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    public_holiday_employee_sync = fields.Boolean(
        string="Apply Employee Public Holidays",
        default=True,
        help="If checked, the region-scoped public holidays are generated as "
        "personal time off for the employees on this working schedule. The "
        "nationwide public holidays are generated company-wide and reach this "
        "schedule either way.",
    )
    public_holiday_overview_line_ids = fields.Many2many(
        "calendar.public.holiday.line",
        string="Public Holiday Overview",
        compute="_compute_public_holiday_overview_line_ids",
        help="The public holidays that reach this working schedule: the "
        "nationwide ones of its companies, on the days the schedule "
        "actually works.",
    )

    @api.depends(
        "company_id",
        "company_id.country_id",
        "attendance_ids.dayofweek",
        "attendance_ids.display_type",
        "flexible_hours",
    )
    def _compute_public_holiday_overview_line_ids(self):
        # The always-true leaf keeps the no-search-all check quiet; the reach
        # of a schedule spans every year the calendar holds.
        lines = self.env["calendar.public.holiday.line"].search([("id", "!=", 0)])
        nationwide = lines.filtered(lambda line: not line._has_public_holiday_scope())
        for calendar in self:
            # The nationwide days plus the ones listing this schedule.
            reachable = nationwide | lines.filtered(
                lambda line, calendar=calendar: calendar
                in line.additional_resource_calendar_ids
            )
            calendar.public_holiday_overview_line_ids = (
                calendar._filter_public_holiday_overview_lines(reachable)
            )

    def _public_holiday_overview_weekdays(self):
        """Weekdays this schedule works on, or ``None`` when every day counts.

        A flexible schedule has no fixed days, so no day can be ruled out.
        """
        self.ensure_one()
        if self.flexible_hours:
            return None
        attendances = self.attendance_ids.filtered(
            lambda attendance: not attendance.display_type
        )
        if not attendances:
            return None
        return {int(attendance.dayofweek) for attendance in attendances}

    def _filter_public_holiday_overview_lines(self, lines):
        """The subset of ``lines`` that reaches this schedule.

        A public holiday on a day the schedule never works -- a Friday
        holiday on a Monday-to-Thursday schedule, say -- changes nothing for
        the people on it, so it is left out of the overview.
        """
        self.ensure_one()
        companies = self._public_holiday_companies()
        weekdays = self._public_holiday_overview_weekdays()
        return lines.filtered(
            lambda line: (weekdays is None or line.date.weekday() in weekdays)
            and any(
                self._matches_public_holiday_country(line, company)
                for company in companies
            )
        )

    def _matches_public_holiday_country(self, line, company):
        self.ensure_one()
        holiday_country = line.public_holiday_id.country_id
        if not holiday_country:
            return True
        country = self.company_id.country_id or company.country_id
        # An unknown company country cannot rule the holiday out. Refusing it
        # there would silently generate nothing at all, which is the far worse
        # failure; `_public_holiday_sync_issues` reports it instead so the
        # country can be filled in.
        return not country or holiday_country == country

    def _public_holiday_companies(self):
        """Companies a mirror has to be created for, per calendar.

        A schedule owned by a company only concerns that company. A shared
        schedule (no company) concerns every company, because
        ``_leave_intervals_batch`` scopes global time off by company at read
        time and ``_check_compare_dates`` compares companies for equality.
        """
        self.ensure_one()
        if self.company_id:
            return self.company_id
        # Every company genuinely has to be walked here; the always-true leaf
        # keeps the no-search-all check quiet.
        return self.env["res.company"].sudo().search([("id", "!=", 0)])

    @api.model_create_multi
    def create(self, vals_list):
        calendars = super().create(vals_list)
        calendars._trigger_public_holiday_sync()
        return calendars

    def write(self, vals):
        res = super().write(vals)
        if SYNC_TRIGGER_FIELDS.intersection(vals):
            self._trigger_public_holiday_sync()
        return res

    def _trigger_public_holiday_sync(self):
        if self.env.context.get("public_holiday_sync"):
            return
        lines = self.env["calendar.public.holiday.line"]._get_lines_to_sync()
        if lines:
            lines._sync_global_leaves(calendars=self)
