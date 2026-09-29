# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from .common import TestPublicHolidayResourceCommon


class TestApplicableCalendars(TestPublicHolidayResourceCommon):
    """The template says which working schedules its holidays reach.

    A nationwide public holiday is generated company-wide, so it reaches
    every schedule of a matching company -- the smart button reflects the
    reach, not any per-schedule opt-in.
    """

    def test_no_line_applies_to_nothing(self):
        self.assertEqual(self.holiday.resource_calendar_count, 0)
        self.assertFalse(self.holiday._get_applicable_resource_calendars())

    def test_a_nationwide_holiday_reaches_every_fixture_schedule(self):
        self._create_line(date(self.year, 10, 3))
        applicable = self.holiday._get_applicable_resource_calendars()
        for calendar in (self.cal_national, self.cal_by, self.cal_tokyo):
            self.assertIn(calendar, applicable)

    def test_a_regional_holiday_is_put_on_no_schedule(self):
        """It belongs to the people working in the region, not to a schedule."""
        self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        self.holiday.invalidate_recordset(["resource_calendar_count"])
        self.assertFalse(self.holiday._get_applicable_resource_calendars())

    def test_a_disabled_line_is_left_out(self):
        line = self._create_line(date(self.year, 10, 3))
        line.active = False
        self.holiday.invalidate_recordset(["resource_calendar_count"])
        self.assertFalse(self.holiday._get_applicable_resource_calendars())

    def test_the_employee_opt_out_does_not_shrink_the_reach(self):
        """The company-wide record reaches the schedule either way."""
        self.cal_tokyo.public_holiday_employee_sync = False
        self._create_line(date(self.year, 10, 3))
        self.assertIn(self.cal_tokyo, self.holiday._get_applicable_resource_calendars())

    def test_another_country_applies_to_nothing(self):
        foreign = self.holiday_model.create(
            {"year": self.year, "country_id": self.other_country.id}
        )
        self._create_line(date(self.year, 7, 14), name="Bastille", holiday=foreign)
        applicable = foreign._get_applicable_resource_calendars()
        for calendar in (self.cal_national, self.cal_by, self.cal_tokyo):
            self.assertNotIn(calendar, applicable)

    def test_the_button_opens_exactly_the_applicable_schedules(self):
        self._create_line(date(self.year, 10, 3), name="Nationwide")
        action = self.holiday.action_view_resource_calendars()
        self.assertEqual(action["res_model"], "resource.calendar")
        self.assertEqual(
            set(self.env["resource.calendar"].search(action["domain"]).ids),
            set(self.holiday._get_applicable_resource_calendars().ids),
        )

    def test_the_count_matches_the_reach(self):
        self._create_line(date(self.year, 10, 3), name="Nationwide")
        self.holiday.invalidate_recordset(["resource_calendar_count"])
        self.assertEqual(
            self.holiday.resource_calendar_count,
            len(self.holiday._get_applicable_resource_calendars()),
        )
