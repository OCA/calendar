# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

import pytz

from .common import TestPublicHolidayResourceCommon


class TestSyncBasic(TestPublicHolidayResourceCommon):
    def _assert_local_full_day(self, leave, day, tz_name):
        """The mirror must span the whole local day of ``tz_name``."""
        tz = pytz.timezone(tz_name)
        start = pytz.utc.localize(leave.date_from).astimezone(tz)
        stop = pytz.utc.localize(leave.date_to).astimezone(tz)
        self.assertEqual(start.date(), day)
        self.assertEqual((start.hour, start.minute), (0, 0))
        self.assertEqual(stop.date(), day)
        self.assertEqual((stop.hour, stop.minute, stop.second), (23, 59, 59))
        self.assertEqual(
            stop.microsecond, 0, "the standard form stores second precision"
        )

    def test_create_line_generates_one_mirror_per_company(self):
        day = date(self.year, 10, 3)
        line = self._create_line(day, name="Tag der deutschen Einheit")
        mirrors = self._mirrors(line)
        self.assertEqual(mirrors.company_id, self.company | self.company_2)
        self.assertEqual(len(mirrors), 2, "exactly one record per company")
        for mirror in mirrors:
            self.assertFalse(mirror.calendar_id, "the working hours stay empty")
            self.assertFalse(mirror.resource_id)
            self.assertEqual(mirror.name, "Tag der deutschen Einheit")

    def test_mirror_spans_the_company_main_schedule_day(self):
        day = date(self.year, 10, 3)
        self.cal_company_2.tz = "Asia/Tokyo"
        line = self._create_line(day)
        self._assert_local_full_day(
            self._company_mirror(line, self.company), day, "Europe/Berlin"
        )
        self._assert_local_full_day(
            self._company_mirror(line, self.company_2), day, "Asia/Tokyo"
        )

    def test_schedule_entry_spans_the_calendar_own_timezone(self):
        day = date(self.year, 10, 3)
        line = self._create_line(day, regions=self.region_nw, calendars=self.cal_tokyo)
        self._assert_local_full_day(
            self._mirrors(line, calendar=self.cal_tokyo), day, "Asia/Tokyo"
        )

    def test_schedule_entry_timezone_with_distant_user_timezone(self):
        """Regression for hr_holidays._prepare_public_holidays_values.

        That hook re-interprets the wall clock of a global time off carrying a
        schedule on create using ``self.env.user.tz``. Building the datetimes
        naively in the calendar timezone would be shifted a second time by it.
        """
        self.env.user.tz = "Europe/Berlin"
        cal_nz = self._create_calendar("Auckland", self.company, tz="Pacific/Auckland")
        day = date(self.year, 10, 3)
        line = self._create_line(day, regions=self.region_nw, calendars=cal_nz)
        self._assert_local_full_day(
            self._mirrors(line, calendar=cal_nz), day, "Pacific/Auckland"
        )

    def test_write_date_moves_mirrors(self):
        line = self._create_line(date(self.year, 10, 3))
        line.date = date(self.year, 10, 7)
        self._assert_local_full_day(
            self._company_mirror(line),
            date(self.year, 10, 7),
            "Europe/Berlin",
        )

    def test_write_name_keeps_mirror_ids(self):
        line = self._create_line(date(self.year, 10, 3))
        before = set(self._mirrors(line).ids)
        line.name = "Renamed"
        after = self._mirrors(line)
        self.assertEqual(set(after.ids), before)
        self.assertEqual(set(after.mapped("name")), {"Renamed"})

    def test_unlink_line_removes_mirrors(self):
        line = self._create_line(date(self.year, 10, 3))
        mirror_ids = self._mirrors(line).ids
        line.unlink()
        self.assertFalse(self.leave_model.search([("id", "in", mirror_ids)]))

    def test_unlink_parent_removes_mirrors(self):
        line = self._create_line(date(self.year, 10, 3))
        mirror_ids = self._mirrors(line).ids
        self.holiday.unlink()
        self.assertFalse(self.leave_model.search([("id", "in", mirror_ids)]))

    def test_sync_is_idempotent(self):
        line = self._create_line(date(self.year, 10, 3))
        before = set(self._mirrors(line).ids)
        line._sync_global_leaves()
        line._sync_global_leaves()
        self.assertEqual(set(self._mirrors(line).ids), before)

    def test_line_before_window_is_not_materialised(self):
        old_holiday = self.holiday_model.create(
            {"year": self.year - 1, "country_id": self.country.id}
        )
        line = self._create_line(date(self.year - 1, 10, 3), holiday=old_holiday)
        self.assertFalse(self._mirrors(line))

    def test_new_company_gets_existing_lines(self):
        line = self._create_line(date(self.year, 10, 3))
        newcomer = self.env["res.company"].create(
            {"name": "Newcomer", "country_id": self.country.id}
        )
        self.env.user.company_ids |= newcomer
        self.assertTrue(self._company_mirror(line, newcomer))

    def test_a_nationwide_line_listing_schedules_stays_company_wide(self):
        """The company-wide record already reaches every schedule."""
        line = self._create_line(
            date(self.year, 10, 3), name="Shift day", calendars=self.cal_tokyo
        )
        self.assertTrue(self._company_mirror(line))
        self.assertFalse(
            self._mirrors(line, calendar=self.cal_tokyo),
            "no schedule entry on top of the company-wide record",
        )

    def test_a_regional_line_listing_a_schedule_reaches_it(self):
        line = self._create_line(
            date(self.year, 10, 3),
            name="Shift day",
            regions=self.region_nw,
            calendars=self.cal_tokyo,
        )
        entry = self._mirrors(line, calendar=self.cal_tokyo)
        self.assertEqual(len(entry), 1)
        self.assertFalse(self._company_mirror(line), "a regional line")
        self.assertFalse(self._mirrors(line, calendar=self.cal_national))

    def test_listing_a_schedule_adds_and_removes_its_entry(self):
        line = self._create_line(
            date(self.year, 10, 3),
            name="Shift day",
            regions=self.region_nw,
            calendars=self.cal_tokyo,
        )
        self.assertTrue(self._mirrors(line, calendar=self.cal_tokyo))
        line.additional_resource_calendar_ids = [(4, self.cal_national.id)]
        self.assertTrue(self._mirrors(line, calendar=self.cal_national))
        line.additional_resource_calendar_ids = [(3, self.cal_tokyo.id)]
        self.assertFalse(self._mirrors(line, calendar=self.cal_tokyo))

    def test_no_schedule_entry_when_a_company_record_covers_the_day(self):
        """A company-wide record already applies to every schedule."""
        day = date(self.year, 10, 3)
        listed = self._create_line(
            day,
            name="Shift day",
            regions=self.region_nw,
            calendars=self.cal_national,
        )
        national = self._create_line(day, name="National")
        self.assertTrue(self._company_mirror(national))
        self.assertFalse(
            self._mirrors(listed),
            "the schedule already has the day through the company-wide record",
        )
        # Removing the nationwide day brings the schedule entry back.
        national.unlink()
        self.assertTrue(self._mirrors(listed, calendar=self.cal_national))
