# Copyright 2015 iDT LABS (http://www.@idtlabs.sl)
# Copyright 2017-2018 Tecnativa - Pedro M. Baeza
# Copyright 2018 Brainbean Apps
# Copyright 2020 InitOS Gmbh
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.exceptions import UserError, ValidationError

from odoo.addons.base.tests.common import BaseCommon


class TestCalendarPublicHoliday(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.holiday_model = cls.env["calendar.public.holiday"]
        cls.holiday_line_model = cls.env["calendar.public.holiday.line"]
        cls.calendar_event = cls.env["calendar.event"]
        cls.wizard_next_year = cls.env["calendar.public.holiday.next.year"]

        # Remove possibly existing public holidays that would interfer.
        cls.holiday_line_model.search([]).unlink()
        cls.holiday_model.search([]).unlink()
        cls.calendar_event.search([]).unlink()

        cls.country_1 = cls.env["res.country"].create(
            {
                "name": "Country 1",
                "code": "XX",
            }
        )
        cls.country_2 = cls.env["res.country"].create(
            {
                "name": "Country 2",
                "code": "YY",
            }
        )
        cls.country_3 = cls.env["res.country"].create(
            {
                "name": "Country 3",
                "code": "ZZ",
            }
        )
        cls.res_partner = cls.env["res.partner"].create(
            {"name": "Partner 1", "country_id": cls.country_1.id}
        )
        cls.holiday_1 = cls.holiday_model.create(
            {
                "year": 2024,
                "country_id": cls.country_1.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Christmas Day for Country 1",
                            "date": "2024-12-25",
                        },
                    )
                ],
            }
        )
        cls.holiday_2 = cls.holiday_model.create(
            {
                "year": 2024,
                "country_id": cls.country_2.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Christmas Day for Country 2",
                            "date": "2024-12-25",
                        },
                    )
                ],
            }
        )
        cls.holiday_3 = cls.holiday_model.create({"year": 2025})
        ls_dates = ["2025-01-02", "2025-01-05", "2025-01-07"]
        for i in range(len(ls_dates)):
            cls.holiday_line_model.create(
                {
                    "name": f"Public Holiday Line {i + 1}",
                    "date": ls_dates[i],
                    "public_holiday_id": cls.holiday_3.id,
                }
            )

    def test_display_name(self):
        holiday_1_display_name = self.holiday_1.display_name
        expect_display_name = (
            f"{self.holiday_1.year} ({self.holiday_1.country_id.name})"
        )
        self.assertEqual(holiday_1_display_name, expect_display_name)

        # without country
        holiday_3_display_name = self.holiday_3.display_name
        expect_display_name = f"{self.holiday_3.year}"
        self.assertEqual(holiday_3_display_name, expect_display_name)

    def test_duplicate_year_country_fail(self):
        # ensures that duplicate year cannot be created for the same country
        with self.assertRaises(ValidationError):
            # same year with country = False
            self.holiday_model.create({"year": 2025})
        with self.assertRaises(ValidationError):
            # same country with holiday_1
            self.holiday_model.create({"year": 2024, "country_id": self.country_1.id})

    def test_duplicate_date_state_fail(self):
        # ensures that duplicate date cannot be created for the same country
        # state or with state null
        holiday_4 = self.holiday_model.create(
            {"year": 2024, "country_id": self.country_3.id}
        )
        holiday_4_line = self.holiday_line_model.create(
            {
                "name": "holiday x",
                "date": "2024-12-25",
                "public_holiday_id": holiday_4.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.holiday_line_model.create(
                {
                    "name": "holiday x",
                    "date": "2024-12-25",
                    "public_holiday_id": holiday_4.id,
                }
            )
        holiday_4_line.state_ids = [(6, 0, [self.country_3.id])]
        with self.assertRaises(ValidationError):
            self.holiday_line_model.create(
                {
                    "name": "holiday x",
                    "date": "2024-12-25",
                    "public_holiday_id": holiday_4.id,
                    "state_ids": [(6, 0, [self.country_3.id])],
                }
            )

    def test_holiday_in_country(self):
        # ensures that correct holidays are identified for a country
        self.assertTrue(
            self.holiday_model.is_public_holiday(
                date(2024, 12, 25), partner_id=self.res_partner.id
            )
        )
        self.assertFalse(
            self.holiday_model.is_public_holiday(
                date(2024, 12, 23), partner_id=self.res_partner.id
            )
        )

    def test_holiday_line_same_year_with_parent(self):
        # ensures that line year and holiday year are the same
        with self.assertRaises(ValidationError):
            self.holiday_model.create(
                {
                    "year": 2026,
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "Line with not the same year",
                                "date": "2027-12-25",
                            },
                        )
                    ],
                }
            )

    def test_list_holidays_in_list_country_specific(self):
        # ensures that correct holidays are identified for a country
        lines = self.holiday_model.get_holidays_list(
            2024, partner_id=self.res_partner.id
        )
        res = lines.filtered(lambda r: r.date == date(2024, 12, 25))
        self.assertEqual(len(res), 1)
        self.assertEqual(len(lines), 1)

    def test_list_holidays_in_list(self):
        # ensures that correct holidays are identified for a country
        lines = self.holiday_model.get_holidays_list(2025)
        res = lines.filtered(lambda r: r.date == date(2025, 1, 2))
        self.assertEqual(len(res), 1)
        self.assertEqual(len(lines), 3)

    def test_create_year_2026_public_holidays(self):
        # holiday_1 and holiday_2 have the same line in 2024 but different country
        ph_start_ids = self.holiday_model.search([("year", "=", 2024)])
        vals = {"public_holiday_ids": ph_start_ids, "year": 2026}
        wizard = self.wizard_next_year.new(values=vals)
        wizard.create_public_holidays()
        lines = self.holiday_model.get_holidays_list(2026)
        self.assertEqual(len(lines), 2)
        res = lines.filtered(
            lambda r: r.public_holiday_id.country_id.id == self.country_1.id
        )
        self.assertEqual(len(res), 1)

    def test_create_year_2027_public_holidays(self):
        # holiday_3 have 3 line in year 2025
        ph_start_ids = self.holiday_model.search([("year", "=", 2025)])
        wizard = self.wizard_next_year.new(
            values={
                "public_holiday_ids": ph_start_ids,
                "year": 2027,
            }
        )
        wizard.create_public_holidays()
        lines = self.holiday_model.get_holidays_list(2027)
        self.assertEqual(len(lines), 3)

    def test_february_29th(self):
        # Ensures that users get a UserError (not a nasty Exception) when
        # trying to create public holidays from year including 29th of
        # February
        holiday_tw_2024 = self.holiday_model.create(
            {"year": 2024, "country_id": self.country_3.id}
        )
        self.holiday_line_model.create(
            {
                "name": "Peace Memorial Holiday",
                "date": "2024-02-29",
                "public_holiday_id": holiday_tw_2024.id,
            }
        )
        vals = {"public_holiday_ids": holiday_tw_2024}
        wz_create_ph = self.wizard_next_year.new(values=vals)

        with self.assertRaises(UserError):
            wz_create_ph.create_public_holidays()

    def test_calendar_event_created(self):
        holiday_1_line = self.holiday_1.line_ids[0]
        meeting_id = holiday_1_line.meeting_id
        self.assertTrue(meeting_id)
        holiday_1_line.unlink()
        self.assertFalse(meeting_id.exists())
        all_lines = self.holiday_line_model.search([])
        categ_id = self.env.ref("calendar_public_holiday.event_type_holiday", False)
        all_meetings = self.calendar_event.search([("categ_ids", "in", categ_id.id)])
        self.assertEqual(len(all_lines), len(all_meetings))
