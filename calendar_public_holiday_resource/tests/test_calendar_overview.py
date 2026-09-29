# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from .common import TestPublicHolidayResourceCommon


class TestCalendarOverview(TestPublicHolidayResourceCommon):
    """The read-only overview on the working schedule form.

    It shows the days that reach the schedule -- the nationwide public
    holidays of its companies, on the days the schedule actually works; the
    regional reach through the employees is added by
    ``hr_holidays_public_resource``.
    """

    def _weekday(self, weekday, offset_weeks=0):
        """A date of the given weekday well inside the current year."""
        day = date(self.year, 3, 1)
        while day.weekday() != weekday:
            day += timedelta(days=1)
        return day + timedelta(weeks=offset_weeks)

    def _overview(self, calendar):
        calendar.invalidate_recordset(["public_holiday_overview_line_ids"])
        return calendar.public_holiday_overview_line_ids

    def test_nationwide_line_shows_on_matching_schedules(self):
        line = self._create_line(self._weekday(0))
        for calendar in (self.cal_national, self.cal_by, self.cal_tokyo):
            self.assertIn(line, self._overview(calendar))

    def test_foreign_country_is_ruled_out(self):
        foreign = self.holiday_model.create(
            {"year": self.year, "country_id": self.other_country.id}
        )
        line = self._create_line(self._weekday(0), name="Bastille", holiday=foreign)
        self.assertNotIn(line, self._overview(self.cal_national))

    def test_countryless_calendar_shows_everywhere(self):
        worldwide = self.holiday_model.create({"year": self.year})
        line = self._create_line(self._weekday(0), name="Worldwide", holiday=worldwide)
        self.assertIn(line, self._overview(self.cal_national))

    def test_shared_schedule_matches_through_any_company(self):
        shared = self._create_calendar("Shared", None)
        line = self._create_line(self._weekday(0))
        self.assertIn(line, self._overview(shared))

    def test_a_disabled_line_is_left_out(self):
        line = self._create_line(self._weekday(0))
        self.assertIn(line, self._overview(self.cal_national))
        line.active = False
        self.assertNotIn(line, self._overview(self.cal_national))

    def test_a_regional_line_is_not_counted_here(self):
        """Its reach goes through people, which this module cannot see."""
        line = self._create_line(
            self._weekday(0), name="Fronleichnam", regions=self.region_by
        )
        self.assertNotIn(line, self._overview(self.cal_by))

    def test_a_day_off_the_schedule_is_left_out(self):
        """The default schedules work Monday to Friday, never Saturday."""
        saturday = self._create_line(self._weekday(5), name="Saturday holiday")
        monday = self._create_line(self._weekday(0), name="Monday holiday")
        overview = self._overview(self.cal_national)
        self.assertIn(monday, overview)
        self.assertNotIn(saturday, overview)

    def test_removing_the_day_removes_its_holidays(self):
        line = self._create_line(self._weekday(4), name="Friday holiday")
        self.assertIn(line, self._overview(self.cal_national))
        self.cal_national.attendance_ids.filtered(
            lambda attendance: attendance.dayofweek == "4"
        ).unlink()
        self.assertNotIn(line, self._overview(self.cal_national))

    def test_a_flexible_schedule_keeps_every_day(self):
        """No fixed days means no day can be ruled out."""
        self.cal_national.flexible_hours = True
        line = self._create_line(self._weekday(5), name="Saturday holiday")
        self.assertIn(line, self._overview(self.cal_national))

    def test_overview_is_readonly(self):
        field = self.env["resource.calendar"]._fields[
            "public_holiday_overview_line_ids"
        ]
        self.assertTrue(field.compute)
        self.assertTrue(field.readonly)
        self.assertFalse(field.store)
