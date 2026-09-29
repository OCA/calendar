# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime

from odoo.exceptions import UserError

from .common import TestPublicHolidayResourceCommon


class TestSyncReadonly(TestPublicHolidayResourceCommon):
    def setUp(self):
        super().setUp()
        self.line = self._create_line(date(self.year, 10, 3))
        self.mirror = self._company_mirror(self.line)

    def test_write_on_mirror_is_rejected(self):
        with self.assertRaises(UserError):
            self.mirror.name = "Manually renamed"

    def test_unlink_on_mirror_is_rejected(self):
        with self.assertRaises(UserError):
            self.mirror.unlink()

    def test_create_with_line_reference_is_rejected(self):
        with self.assertRaises(UserError):
            self.leave_model.create(
                {
                    "name": "Smuggled in",
                    "calendar_id": self.cal_by.id,
                    "date_from": datetime(self.year, 10, 6, 0, 0, 0),
                    "date_to": datetime(self.year, 10, 6, 23, 59, 59),
                    "public_holiday_line_id": self.line.id,
                }
            )

    def test_sync_context_may_write(self):
        self.mirror.with_context(public_holiday_sync=True).name = "Renamed"
        self.assertEqual(self.mirror.name, "Renamed")

    def test_unmanaged_leave_is_untouched(self):
        manual = self.leave_model.create(
            {
                "name": "Company outing",
                "calendar_id": self.cal_national.id,
                "date_from": datetime(self.year, 5, 2, 0, 0, 0),
                "date_to": datetime(self.year, 5, 2, 23, 59, 59),
            }
        )
        manual.name = "Company party"
        self.assertEqual(manual.name, "Company party")
        manual.unlink()
