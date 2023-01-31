# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from freezegun import freeze_time

from odoo.tests.common import TransactionCase


class ResourceCombinationWizardCase(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        # calendar have default attendance_ids, force it to have none.
        self.full_calendar = self.env["resource.calendar"].create(
            {"name": "full-time", "attendance_ids": False}
        )
        for day in range(7):
            self.env["resource.calendar.attendance"].create(
                {
                    "name": "attendance",
                    "dayofweek": str(day),
                    "hour_from": 0,
                    "hour_to": 12,
                    "calendar_id": self.full_calendar.id,
                }
            )
            self.env["resource.calendar.attendance"].create(
                {
                    "name": "attendance",
                    "dayofweek": str(day),
                    "hour_from": 12,
                    "hour_to": 24,
                    "calendar_id": self.full_calendar.id,
                }
            )
        self.workweek_calendar = self.env["resource.calendar"].create(
            {"name": "workweek", "attendance_ids": False}
        )
        for day in range(5):
            self.env["resource.calendar.attendance"].create(
                {
                    "name": "attendance",
                    "dayofweek": str(day),
                    "hour_from": 8,
                    "hour_to": 12,
                    "calendar_id": self.full_calendar.id,
                }
            )
            self.env["resource.calendar.attendance"].create(
                {
                    "name": "attendance",
                    "dayofweek": str(day),
                    "hour_from": 13,
                    "hour_to": 17,
                    "calendar_id": self.full_calendar.id,
                }
            )
        self.user_1 = self.env["res.users"].create(
            {
                "name": "User 1",
                "login": "user1",
                "password": "user1",
            }
        )
        self.user_2 = self.env["res.users"].create(
            {
                "name": "User 2",
                "login": "user2",
                "password": "user2",
            }
        )
        self.room_1 = self.env["resource.resource"].create(
            {
                "name": "room 1",
                "resource_type": "material",
                "calendar_id": self.full_calendar.id,
            }
        )
        self.room_2 = self.env["resource.resource"].create(
            {
                "name": "room 2",
                "resource_type": "material",
                "calendar_id": self.full_calendar.id,
            }
        )
        self.worker_1 = self.env["resource.resource"].create(
            {
                "name": "worker 1",
                "user_id": self.user_1.id,
                "resource_type": "user",
                "calendar_id": self.workweek_calendar.id,
            }
        )
        self.worker_2 = self.env["resource.resource"].create(
            {
                "name": "worker 2",
                "user_id": self.user_2.id,
                "resource_type": "user",
                "calendar_id": self.workweek_calendar.id,
            }
        )
        self.partner_1 = self.env["res.partner"].create(
            {
                "name": "partner 1",
            }
        )
        self.booking_type_1 = self.env["resource.booking.type"].create(
            {
                "name": "booking type 1",
            }
        )
        self.room_category = self.env["resource.category"].create(
            {
                "name": "room",
                "resource_ids": [
                    (6, 0, [self.room_1.id, self.room_2.id]),
                ],
            }
        )
        self.worker_category = self.env["resource.category"].create(
            {
                "name": "worker",
                "resource_ids": [
                    (6, 0, [self.worker_1.id, self.worker_2.id]),
                ],
            }
        )

    def test_create_resource_combination(self):
        """
        Selecting available resources should create a new resource combination
        and assign it to the booking.
        """

    def test_find_existing_resource_combination(self):
        """
        Selecting available resources should use a corresponding existing
        resource combination if one exists and assign it to the booking.
        """

    def test_no_available_resources_found(self):
        """
        If no matching available resources are found, no resource combination
        should be created nor assigned to the booking.
        """

    def test_re_select_current_combination(self):
        """
        When changing the resource combination of a booking, the currently
        assigned resources should be considered as available for the booking.
        """

    def test_select_resource_in_multiple_selected_categories(self):
        """
        When a resource matches several selected resource categories, it
        should appear several times in the list of available resources, but
        selecting it for one category should make it unavailable for the
        others.
        """

    def test_unique_resource_category(self):
        """
        It should be impossible to select a resource category that has been
        already selected.
        """

    def test_no_categories_selected(self):
        """
        When no categories are selected, it should go to a special step that
        displays an error message, and allows only to go back or cancel.
        """

    @freeze_time("2023-01-31 12:00:00")
    def test_resource_available(self):
        booking = self.env["resource.booking"].create(
            {
                "partner_id": self.partner_1.id,
                "type_id": self.booking_type_1.id,
                "start": "2023-02-06 10:00:00",
                "duration": 2,
            }
        )
        wizard = (
            self.env["resource.booking.combination.wizard"]
            .with_context({"active_id": booking.id})
            .create({})
        )
        # todo: continue writing test
