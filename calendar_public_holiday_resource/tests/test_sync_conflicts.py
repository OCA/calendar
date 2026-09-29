# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime

from .common import TestPublicHolidayResourceCommon


class TestSyncConflicts(TestPublicHolidayResourceCommon):
    def _manual_leave(self, day, calendar, name="Manual", date_to=None, company=None):
        company = company or self.company
        leave = self.leave_model.with_company(company).create(
            {
                "name": name,
                "calendar_id": calendar.id if calendar else False,
                "date_from": datetime(day.year, day.month, day.day, 0, 0, 0),
                "date_to": date_to
                or datetime(day.year, day.month, day.day, 23, 59, 59),
            }
        )
        # `company_id` is a stored compute that ignores an explicit value, so
        # a company-wide record has to be pinned after the fact.
        leave.write({"company_id": company.id})
        return leave

    def test_company_wide_manual_leave_is_adopted(self):
        day = date(self.year, 10, 3)
        manual = self._manual_leave(day, None, name="Holiday")
        line = self._create_line(day)
        self.assertEqual(manual.public_holiday_line_id, line)
        self.assertFalse(manual.calendar_id, "the record stays company-wide")
        self.assertEqual(self._company_mirror(line), manual)
        # The other company gets a freshly created record.
        self.assertTrue(self._company_mirror(line, self.company_2))

    def test_adoption_ignores_name_case_and_spacing(self):
        day = date(self.year, 10, 3)
        manual = self._manual_leave(day, None, name="  HOLIDAY ")
        line = self._create_line(day)
        self.assertEqual(manual.public_holiday_line_id, line)

    def test_adoption_preserves_the_record_id(self):
        day = date(self.year, 10, 3)
        manual = self._manual_leave(day, None, name="Holiday")
        manual_id = manual.id
        line = self._create_line(day)
        self.assertEqual(self._company_mirror(line).id, manual_id)

    def test_schedule_scoped_manual_leave_is_widened(self):
        """A same-day record on one schedule becomes the company-wide mirror.

        Everybody it covered keeps the day and the rest of the company gains
        it, which is what the public holiday means. Leaving it alone instead
        would trip the standard overlap constraint on the company-wide record.
        """
        day = date(self.year, 10, 3)
        manual = self._manual_leave(day, self.cal_national, name="Holiday")
        line = self._create_line(day)
        self.assertEqual(manual.public_holiday_line_id, line)
        self.assertFalse(manual.calendar_id, "the record is widened")
        self.assertEqual(self._company_mirror(line), manual)

    def test_different_name_on_same_day_is_reported_not_adopted(self):
        """A bridge day or an event is not this public holiday entered by hand."""
        day = date(self.year, 10, 3)
        manual = self._manual_leave(day, self.cal_national, name="Bridge day")
        line = self._create_line(day)
        self.assertFalse(manual.public_holiday_line_id)
        # Creating the company-wide mirror next to it would trip the standard
        # overlap constraint, so the company is skipped and reported ...
        self.assertFalse(self._company_mirror(line))
        summary = line._sync_global_leaves(dry_run=True)
        self.assertTrue(
            any(conflict["leave_id"] == manual.id for conflict in summary["conflicts"])
        )
        # ... while the unaffected company gets its record normally.
        self.assertTrue(self._company_mirror(line, self.company_2))

    def test_multi_day_manual_leave_is_reported_not_adopted(self):
        day = date(self.year, 12, 27)
        shutdown = self._manual_leave(
            date(self.year, 12, 24),
            None,
            name="Christmas shutdown",
            date_to=datetime(self.year, 12, 31, 23, 59, 59),
        )
        line = self._create_line(day, name="Between the years")
        self.assertFalse(shutdown.public_holiday_line_id)
        self.assertFalse(self._company_mirror(line))
        summary = line._sync_global_leaves(dry_run=True)
        self.assertTrue(
            any(
                conflict["leave_id"] == shutdown.id for conflict in summary["conflicts"]
            )
        )

    def test_midnight_boundary_leave_is_treated_as_conflict(self):
        """A record ending at the next midnight overlaps by exactly one second."""
        day = date(self.year, 10, 3)
        manual = self._manual_leave(
            day,
            None,
            date_to=datetime(self.year, 10, 4, 0, 0, 0),
        )
        line = self._create_line(day)
        self.assertFalse(manual.public_holiday_line_id)
        self.assertFalse(self._company_mirror(line))

    def test_schedule_entry_adopts_a_record_on_its_schedule(self):
        """A hand-made record scoped to the listed schedule is adopted."""
        day = date(self.year, 10, 3)
        manual = self._manual_leave(day, self.cal_national, name="Shift day")
        line = self._create_line(
            day,
            name="Shift day",
            regions=self.region_nw,
            calendars=self.cal_national,
        )
        self.assertEqual(manual.public_holiday_line_id, line)
        self.assertEqual(self._mirrors(line, calendar=self.cal_national), manual)

    def test_national_line_wins_over_regional_on_same_day(self):
        day = date(self.year, 10, 3)
        regional = self._create_line(day, name="Regional", regions=self.region_by)
        national = self._create_line(day, name="National")
        self.assertFalse(self._mirrors(regional))
        self.assertTrue(self._company_mirror(national))

    def test_two_regions_on_one_schedule_yield_a_single_mirror(self):
        day = date(self.year, 6, 19)
        both = self._create_calendar("Both", self.company)
        self._set_calendar_regions(both, self.region_by | self.region_nw)
        line_by = self._create_line(day, name="BY", regions=self.region_by)
        line_nw = self._create_line(day, name="NW", regions=self.region_nw)
        mirrors = self.leave_model.search(
            [
                ("calendar_id", "=", both.id),
                ("public_holiday_line_id", "in", (line_by | line_nw).ids),
            ]
        )
        self.assertEqual(len(mirrors), 1)

    def test_moving_a_holiday_onto_an_occupied_day(self):
        """Unlink-before-create keeps the moved mirror from overlapping itself."""
        line = self._create_line(date(self.year, 10, 8), name="Moving")
        other = self._create_line(date(self.year, 10, 7), name="Static")
        other.unlink()
        line.date = date(self.year, 10, 7)
        self.assertEqual(len(self._company_mirror(line)), 1)
