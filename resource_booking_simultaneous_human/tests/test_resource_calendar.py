# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from freezegun import freeze_time

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


@freeze_time("2021-1-1")
class TestResourceCalendar(TransactionCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)

        cls.partner_id = cls.env["res.partner"].create({"name": "Test Partner"})
        partner_of_user = cls.env["res.partner"].create(
            {"name": "Partner of Test User"}
        )
        cls.user_id = cls.env["res.users"].create(
            {
                "login": "test-user@example.com",
                "partner_id": partner_of_user.id,
            }
        )
        cls.calendar_id = cls.env["resource.calendar"].create(
            {
                "name": "Test Calendar",
                "attendance_ids": [
                    (
                        0,
                        False,
                        {
                            "name": "Test Day",
                            "dayofweek": "0",  # Monday
                            "hour_from": 0,
                            "hour_to": 23.99,
                        },
                    )
                ],
            }
        )
        cls.material_resource_id = cls.env["resource.resource"].create(
            {
                "name": "Test Material Resource",
                "resource_type": "material",
            }
        )
        cls.human_resource_id = cls.env["resource.resource"].create(
            {
                "name": "Test Human Resource",
                "resource_type": "user",
                "user_id": cls.user_id.id,
            }
        )
        cls.material_combination_id = cls.env["resource.booking.combination"].create(
            {
                "resource_ids": [cls.material_resource_id.id],
            }
        )
        cls.human_combination_id = cls.env["resource.booking.combination"].create(
            {
                "resource_ids": [cls.human_resource_id.id],
            }
        )
        cls.material_booking_type_id = cls.env["resource.booking.type"].create(
            {
                "name": "Test Material Booking Type",
                "duration": 1,
                "resource_calendar_id": cls.calendar_id.id,
            }
        )
        cls.env["resource.booking.type.combination.rel"].create(
            {
                "combination_id": cls.material_combination_id.id,
                "type_id": cls.material_booking_type_id.id,
            }
        )
        cls.human_booking_type_id = cls.env["resource.booking.type"].create(
            {
                "name": "Test Human Booking Type",
                "duration": 1,
                "resource_calendar_id": cls.calendar_id.id,
            }
        )
        cls.env["resource.booking.type.combination.rel"].create(
            {
                "combination_id": cls.human_combination_id.id,
                "type_id": cls.human_booking_type_id.id,
            }
        )

    def test_simultaneous_booking_human(self):
        """Two bookings can happen simultaneously for human resources."""
        # First.
        self.env["resource.booking"].create(
            {
                "partner_id": self.partner_id.id,
                "type_id": self.human_booking_type_id.id,
                "combination_id": self.human_combination_id.id,
                "combination_auto_assign": False,
                "start": datetime(2021, 3, 1, 9, 0),
            }
        )
        # Second, simultaneously.
        self.env["resource.booking"].create(
            {
                "partner_id": self.partner_id.id,
                "type_id": self.human_booking_type_id.id,
                "combination_id": self.human_combination_id.id,
                "combination_auto_assign": False,
                "start": datetime(2021, 3, 1, 9, 0),
            }
        )

    def test_simultaneous_booking_material(self):
        """Two bookings cannot happen simultaneously for material resources."""
        # First.
        self.env["resource.booking"].create(
            {
                "partner_id": self.partner_id.id,
                "type_id": self.material_booking_type_id.id,
                "combination_id": self.material_combination_id.id,
                "combination_auto_assign": False,
                "start": datetime(2021, 3, 1, 9, 0),
            }
        )
        with self.assertRaises(ValidationError):
            # Second, simultaneously.
            self.env["resource.booking"].create(
                {
                    "partner_id": self.partner_id.id,
                    "type_id": self.human_booking_type_id.id,
                    "combination_id": self.material_combination_id.id,
                    "combination_auto_assign": False,
                    "start": datetime(2021, 3, 1, 9, 0),
                }
            )
