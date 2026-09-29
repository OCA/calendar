# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime

from .common import TestPublicHolidayResourceCommon


class TestDisplayName(TestPublicHolidayResourceCommon):
    """Generated time off names the public holiday calendar it comes from."""

    def test_generated_time_off_names_its_source(self):
        line = self._create_line(date(self.year, 10, 3), name="Tag der Einheit")
        mirror = self._company_mirror(line)
        self.assertEqual(
            mirror.display_name,
            f"[{self.holiday.display_name}] Tag der Einheit",
        )

    def test_the_name_is_not_repeated(self):
        line = self._create_line(date(self.year, 10, 3), name="Tag der Einheit")
        mirror = self._company_mirror(line)
        self.assertEqual(mirror.display_name.count("Tag der Einheit"), 1)

    def test_display_name_follows_a_rename(self):
        line = self._create_line(date(self.year, 10, 3), name="Before")
        mirror = self._company_mirror(line)
        line.name = "After"
        mirror.invalidate_recordset(["display_name"])
        self.assertEqual(mirror.display_name, f"[{self.holiday.display_name}] After")

    def test_hand_made_time_off_is_left_alone(self):
        manual = self.leave_model.create(
            {
                "name": "Company outing",
                "calendar_id": self.cal_national.id,
                "date_from": datetime(self.year, 5, 2, 0, 0, 0),
                "date_to": datetime(self.year, 5, 2, 23, 59, 59),
            }
        )
        self.assertEqual(manual.display_name, "Company outing")
