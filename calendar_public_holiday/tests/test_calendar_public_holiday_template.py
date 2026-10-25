# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.exceptions import ValidationError

from odoo.addons.base.tests.common import BaseCommon


class TestCalendarPublicHolidayTemplate(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.holiday_model = cls.env["calendar.public.holiday"]
        cls.country = cls.env["res.country"].create({"name": "Country 1", "code": "XX"})
        cls.state = cls.env["res.country.state"].create(
            {"name": "State 1", "code": "S1", "country_id": cls.country.id}
        )
        cls.template = cls.env["calendar.public.holiday.template"].create(
            {
                "name": "Country 1",
                "country_id": cls.country.id,
                "line_ids": [
                    (0, 0, {"name": "New Year", "date": "2000-01-01"}),
                    (
                        0,
                        0,
                        {
                            "name": "Christmas",
                            "date": "2000-12-25",
                            "state_ids": [(6, 0, cls.state.ids)],
                        },
                    ),
                    (0, 0, {"name": "Easter Sunday", "date_type": "easter"}),
                    (
                        0,
                        0,
                        {
                            "name": "Good Friday",
                            "date_type": "easter",
                            "day_offset": -2,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Ascension Day",
                            "date_type": "easter",
                            "day_offset": 39,
                        },
                    ),
                ],
            }
        )

    def _get_dates(self, public_holiday):
        return {line.name: line.date for line in public_holiday.line_ids}

    def test_create_public_holidays(self):
        public_holiday = self.template.create_public_holidays(2024)
        self.assertEqual(public_holiday.year, 2024)
        self.assertEqual(public_holiday.country_id, self.country)
        self.assertEqual(
            self._get_dates(public_holiday),
            {
                "New Year": date(2024, 1, 1),
                "Christmas": date(2024, 12, 25),
                "Easter Sunday": date(2024, 3, 31),
                "Good Friday": date(2024, 3, 29),
                "Ascension Day": date(2024, 5, 9),
            },
        )
        lines = public_holiday.line_ids
        christmas = lines.filtered(lambda line: line.name == "Christmas")
        self.assertEqual(christmas.state_ids, self.state)
        self.assertFalse(christmas.variable_date)
        easter = lines.filtered(lambda line: line.name == "Easter Sunday")
        self.assertTrue(easter.variable_date)
        self.assertFalse(easter.state_ids)

    def test_create_public_holidays_replaces_existing(self):
        public_holiday = self.holiday_model.create(
            {
                "year": 2025,
                "country_id": self.country.id,
                "line_ids": [(0, 0, {"name": "Old Holiday", "date": "2025-06-01"})],
            }
        )
        result = self.template.create_public_holidays(2025)
        self.assertEqual(result, public_holiday)
        self.assertNotIn("Old Holiday", public_holiday.line_ids.mapped("name"))
        self.assertEqual(len(public_holiday.line_ids), 5)
        self.assertEqual(
            self._get_dates(public_holiday)["Easter Sunday"], date(2025, 4, 20)
        )

    def test_action_generate_public_holidays(self):
        self.template.generate_year = 2026
        action = self.template.action_generate_public_holidays()
        public_holiday = self.holiday_model.browse(action["res_id"])
        self.assertEqual(public_holiday.year, 2026)
        self.assertEqual(
            self._get_dates(public_holiday)["Good Friday"], date(2026, 4, 3)
        )

    def test_fixed_date_required(self):
        with self.assertRaises(ValidationError):
            self.template.line_ids = [(0, 0, {"name": "No Date"})]

    def test_february_29_not_allowed(self):
        with self.assertRaises(ValidationError):
            self.template.line_ids = [(0, 0, {"name": "Leap", "date": "2000-02-29"})]
