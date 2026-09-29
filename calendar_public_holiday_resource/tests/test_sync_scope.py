# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from .common import TestPublicHolidayResourceCommon


class TestSyncScope(TestPublicHolidayResourceCommon):
    def test_scoped_line_only_reaches_declared_schedule(self):
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        self.assertEqual(self._mirrors(line).calendar_id, self.cal_by)

    def test_scoped_line_ignores_other_region(self):
        cal_nw = self._create_calendar("Nordrhein", self.company, self.region_nw)
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        self.assertFalse(self._mirrors(line, cal_nw))

    def test_national_line_is_generated_company_wide(self):
        line = self._create_line(date(self.year, 10, 3))
        self.assertTrue(self._company_mirror(line))
        # It reaches every schedule through the company-wide record, so no
        # schedule gets a record of its own by default.
        self.assertFalse(self._mirrors(line).calendar_id)

    def test_country_mismatch_produces_nothing(self):
        foreign = self.holiday_model.create(
            {"year": self.year, "country_id": self.other_country.id}
        )
        line = self._create_line(
            date(self.year, 7, 14), name="Bastille", holiday=foreign
        )
        # Every company has a country here, so the holiday matches nobody. A
        # company without a country is deliberately not ruled out, see
        # test_unknown_company_country_still_generates.
        self.assertFalse(self._mirrors(line))

    def test_unknown_company_country_still_generates(self):
        """A company without a country must not silently generate nothing.

        Refusing every public holiday there is indistinguishable from a broken
        installation, so an unknown country cannot rule the holiday out.
        """
        self.company.country_id = False
        line = self._create_line(date(self.year, 10, 3))
        self.assertTrue(self._company_mirror(line))

    def test_country_mismatch_is_reported(self):
        foreign = self.holiday_model.create(
            {"year": self.year, "country_id": self.other_country.id}
        )
        line = self._create_line(
            date(self.year, 7, 14), name="Bastille", holiday=foreign
        )
        summary = line._sync_global_leaves(dry_run=True)
        self.assertTrue(summary["issues"])
        self.assertIn(self.other_country.name, summary["issues"][0])

    def test_employee_opt_out_does_not_stop_the_company_record(self):
        """The nationwide day no longer asks any working schedule."""
        (self.cal_national | self.cal_by | self.cal_tokyo).write(
            {"public_holiday_employee_sync": False}
        )
        line = self._create_line(date(self.year, 10, 3))
        self.assertTrue(self._company_mirror(line))
        summary = line._sync_global_leaves(dry_run=True)
        self.assertFalse(summary["issues"])

    def test_a_scoped_sync_does_not_report_a_covered_region(self):
        """Saving one schedule must not accuse a holiday another one covers.

        Saving a working schedule, hiring someone or moving a work address all
        synchronise a subset. Judging the outcome from that subset reported
        "no working schedule covers ..." for public holidays that were in fact
        generated on a different schedule entirely.
        """
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        self.assertTrue(self._mirrors(line, self.cal_by))
        summary = line._sync_global_leaves(calendars=self.cal_national, dry_run=True)
        self.assertFalse(
            summary["issues"],
            "the region is covered by another working schedule",
        )

    def test_a_scoped_sync_still_reports_a_region_nobody_covers(self):
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_nw
        )
        summary = line._sync_global_leaves(calendars=self.cal_national, dry_run=True)
        self.assertTrue(summary["issues"])
        self.assertIn(self.region_nw.name, summary["issues"][0])

    def test_undeclared_region_is_reported(self):
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_nw
        )
        summary = line._sync_global_leaves(dry_run=True)
        self.assertTrue(
            any(self.region_nw.name in issue for issue in summary["issues"]),
            f"the undeclared region should be named in {summary['issues']}",
        )

    def test_holiday_without_country_reaches_every_company(self):
        worldwide = self.holiday_model.create({"year": self.year})
        line = self._create_line(
            date(self.year, 1, 2), name="Worldwide", holiday=worldwide
        )
        self.assertTrue(self._company_mirror(line, self.company))
        self.assertTrue(self._company_mirror(line, self.company_2))

    def test_employee_sync_disabled_schedule_is_skipped(self):
        self.cal_by.public_holiday_employee_sync = False
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        self.assertFalse(self._mirrors(line))

    def test_reenabling_employee_sync_recreates_mirror(self):
        self.cal_by.public_holiday_employee_sync = False
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        self.cal_by.public_holiday_employee_sync = True
        self.assertTrue(self._mirrors(line, self.cal_by))

    def test_covering_a_region_adds_its_scoped_holiday(self):
        line = self._create_line(
            date(self.year, 6, 19), name="Fronleichnam", regions=self.region_by
        )
        self.assertFalse(self._mirrors(line, self.cal_national))
        # As if an employee of that region joined the schedule.
        self._set_calendar_regions(self.cal_national, self.region_by)
        line._sync_global_leaves()
        self.assertTrue(self._mirrors(line, self.cal_national))

    def test_listed_shared_schedule_gets_one_entry_per_company(self):
        shared = self._create_calendar("Shared", None)
        line = self._create_line(
            date(self.year, 10, 3),
            name="Shift day",
            regions=self.region_nw,
            calendars=shared,
        )
        mirrors = self._mirrors(line, calendar=shared)
        self.assertEqual(mirrors.company_id, self.company | self.company_2)
        self.assertEqual(len(mirrors), 2)
