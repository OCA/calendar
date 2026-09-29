# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from .common import TestPublicHolidayResourceCommon


class TestSyncHardening(TestPublicHolidayResourceCommon):
    def test_new_company_gets_mirrors_right_away(self):
        """A new company needs its records at once, not at the nightly cron."""
        line = self._create_line(date(self.year, 10, 3))
        company = self.env["res.company"].create(
            {"name": "Newcomer", "country_id": self.country.id}
        )
        self.env.user.company_ids |= company
        self.assertEqual(len(self._company_mirror(line, company)), 1)

    def test_new_company_gets_schedule_entries_on_shared_calendar(self):
        """A listed shared schedule carries every company."""
        shared = self._create_calendar("Shared", None)
        line = self._create_line(
            date(self.year, 10, 3),
            name="Shift day",
            regions=self.region_nw,
            calendars=shared,
        )
        company = self.env["res.company"].create(
            {"name": "Newcomer", "country_id": self.country.id}
        )
        self.env.user.company_ids |= company
        mirror = self.leave_model.search(
            [
                ("public_holiday_line_id", "=", line.id),
                ("calendar_id", "=", shared.id),
                ("company_id", "=", company.id),
            ]
        )
        self.assertEqual(len(mirror), 1)

    def test_deleting_a_resource_removes_its_mirrors(self):
        """A personal mirror must go with its resource, not become global.

        The foreign key nullifies ``resource_id``, which would silently turn a
        regional public holiday into one for the whole schedule.
        """
        self._set_calendar_regions(self.cal_by, self.region_by)
        resource = self._resources_by_calendar[self.cal_by.id]
        line = self._create_line(
            date(self.year, 8, 15), name="Regional", regions=self.region_by
        )
        self.assertTrue(
            self.leave_model.search(
                [
                    ("public_holiday_line_id", "=", line.id),
                    ("resource_id", "=", resource.id),
                ]
            )
        )
        del self._resources_by_calendar[self.cal_by.id]
        resource.unlink()
        self.assertFalse(
            self.leave_model.search([("public_holiday_line_id", "=", line.id)])
        )

    def test_bulk_deleting_resources_does_not_collide(self):
        """Two nullified mirrors of one line would violate the unique index."""
        self._set_calendar_regions(self.cal_by, self.region_by)
        first = self._resources_by_calendar[self.cal_by.id]
        second = self.env["resource.resource"].create(
            {
                "name": "Second Bayern resource",
                "calendar_id": self.cal_by.id,
                "company_id": self.company.id,
            }
        )
        self._resources_by_calendar[self.cal_by.id] = first | second
        line = self._create_line(
            date(self.year, 8, 15), name="Regional", regions=self.region_by
        )
        mirrors = self.leave_model.search([("public_holiday_line_id", "=", line.id)])
        self.assertEqual(len(mirrors), 2)
        del self._resources_by_calendar[self.cal_by.id]
        (first | second).unlink()
        self.assertFalse(
            self.leave_model.search([("public_holiday_line_id", "=", line.id)])
        )

    def _set_sync_year_from(self, year):
        self.env["ir.config_parameter"].sudo().set_param(
            "calendar_public_holiday_resource.sync_year_from", str(year)
        )

    def test_past_year_mirrors_are_left_alone(self):
        """History survives edits on its line and the nightly cron."""
        self._set_sync_year_from(self.year - 1)
        past_holiday = self.holiday_model.create(
            {"year": self.year - 1, "country_id": self.country.id}
        )
        past_line = self._create_line(date(self.year - 1, 10, 3), holiday=past_holiday)
        mirrors = self._mirrors(past_line)
        self.assertTrue(mirrors)
        self._set_sync_year_from(self.year)
        past_line.name = "Renamed after the fact"
        survivors = self._mirrors(past_line)
        self.assertEqual(set(survivors.ids), set(mirrors.ids))
        # Out of the window means untouched, so the old name stays.
        self.assertEqual(set(survivors.mapped("name")), {"Holiday"})
        self.line_model._cron_sync_global_leaves()
        self.assertEqual(set(self._mirrors(past_line).ids), set(mirrors.ids))
