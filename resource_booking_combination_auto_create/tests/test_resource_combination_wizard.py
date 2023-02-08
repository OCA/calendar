# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from freezegun import freeze_time

from odoo.tests.common import TransactionCase


@freeze_time("2023-01-31 12:00:00")
class ResourceCombinationWizardCase(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        attendances = []
        for day in range(7):
            attendances.append(
                {
                    "name": "attendance",
                    "dayofweek": str(day),
                    "hour_from": 0,
                    "hour_to": 12,
                }
            )
            attendances.append(
                {
                    "name": "attendance",
                    "dayofweek": str(day),
                    "hour_from": 12,
                    "hour_to": 24,
                }
            )
        self.full_calendar = self.env["resource.calendar"].create(
            {
                "name": "full-time",
                "attendance_ids": [(0, 0, vals) for vals in attendances],
                "tz": "UTC",
            }
        )
        attendances = []
        for day in range(5):
            attendances.append(
                {
                    "name": "attendance",
                    "dayofweek": str(day),
                    "hour_from": 8,
                    "hour_to": 12,
                }
            )
            attendances.append(
                {
                    "name": "attendance",
                    "dayofweek": str(day),
                    "hour_from": 13,
                    "hour_to": 17,
                    "calendar_id": self.full_calendar.id,
                }
            )
        self.workweek_calendar = self.env["resource.calendar"].create(
            {
                "name": "workweek",
                "attendance_ids": [(0, 0, vals) for vals in attendances],
                "tz": "UTC",
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
                "resource_calendar_id": self.full_calendar.id,
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

    def _create_resource_combination(self, resources):
        return self.env["resource.booking.combination"].create(
            {
                "resource_ids": [
                    (6, 0, [r.id for r in resources]),
                ],
            }
        )

    def _add_combination_to_booking_type(self, booking_type, resource_combination):
        self.env["resource.booking.type.combination.rel"].create(
            {
                "type_id": booking_type.id,
                "combination_id": resource_combination.id,
            }
        )

    def _create_wizard_with_selected_categories(
        self, resource_booking, resource_categories
    ):
        return (
            self.env["resource.booking.combination.wizard"]
            .with_context({"active_id": resource_booking.id})
            .create(
                {"resource_category_ids": [(6, 0, [r.id for r in resource_categories])]}
            )
        )

    def _get_available_resources_on_current_step(self, wizard):
        return self.env["resource.booking.category.selection.resource"].search(
            [
                (
                    "resource_booking_category_selection_id",
                    "=",
                    wizard.current_resource_booking_category_selection_id.id,
                )
            ]
        )

    def _select_resources_by_index_on_current_step(self, wizard, indexes):
        available_resources = self._get_available_resources_on_current_step(wizard)
        wizard.available_resource_ids = [
            (6, 0, [available_resources[i].id for i in indexes])
        ]

    def _create_resource_booking(self):
        return self.env["resource.booking"].create(
            {
                "partner_id": self.partner_1.id,
                "type_id": self.booking_type_1.id,
                "start": "2023-02-06 10:00:00",
                "duration": 2,
            }
        )

    def test_create_resource_combination(self):
        """
        Selecting available resources should create a new resource combination
        and assign it to the booking.
        """
        booking = self._create_resource_booking()
        wizard = self._create_wizard_with_selected_categories(
            booking, [self.room_category, self.worker_category]
        )
        wizard.open_next()
        self._select_resources_by_index_on_current_step(wizard, [0])
        wizard.open_next()
        self._select_resources_by_index_on_current_step(wizard, [0])
        wizard.open_next()
        wizard.create_combination()
        combination = booking.combination_id
        resources = combination.resource_ids
        self.assertEqual(len(resources), 2)
        self.assertIn(self.room_1, resources)
        self.assertIn(self.worker_1, resources)

    def test_find_existing_resource_combination(self):
        """
        Selecting available resources should use a corresponding existing
        resource combination if one exists and assign it to the booking.
        """
        existing_combination = self._create_resource_combination(
            [self.room_1, self.worker_1]
        )
        self._add_combination_to_booking_type(self.booking_type_1, existing_combination)
        booking = self._create_resource_booking()
        wizard = self._create_wizard_with_selected_categories(
            booking, [self.room_category, self.worker_category]
        )
        wizard.open_next()
        self._select_resources_by_index_on_current_step(wizard, [0])
        wizard.open_next()
        self._select_resources_by_index_on_current_step(wizard, [0])
        wizard.open_next()
        wizard.create_combination()
        combination = booking.combination_id
        self.assertEqual(combination, existing_combination)

    def test_create_resource_combination_if_none_exactly_matching(self):
        """
        It should not use an existing combination if it contains resources
        that have not been selected (in addition to the selected ones).
        """
        combination_2_rooms = self._create_resource_combination(
            [self.room_1, self.room_2]
        )
        self._add_combination_to_booking_type(self.booking_type_1, combination_2_rooms)
        booking = self._create_resource_booking()
        wizard = self._create_wizard_with_selected_categories(
            booking, [self.room_category]
        )
        wizard.open_next()
        self._select_resources_by_index_on_current_step(wizard, [0])
        wizard.open_next()
        wizard.create_combination()
        combination = booking.combination_id
        self.assertNotEqual(combination, combination_2_rooms)
        self.assertEqual(len(combination), 1)

    def test_no_auto_assign_combination(self):
        """
        When creating a booking with a booking type that contains only one
        resource combination, that combination must not be auto-assigned.
        """
        combination = self._create_resource_combination([self.room_1])
        self._add_combination_to_booking_type(self.booking_type_1, combination)
        booking = self._create_resource_booking()
        self.assertFalse(booking.combination_id)

    def test_allow_save_booking_with_meeting_without_combination(self):
        """
        It should be possible to save a resource booking with a date but no
        resource combination.

        This is needed for the wizard, because opening the wizard saves the
        resource booking.
        """
        # note: this condition is checked in an sql constraint and sql
        # constraints are only checked when the transaction is committed, so
        # this test actually does not fail even with the default constraint.
        booking = self._create_resource_booking()
        self.assertTrue(booking.meeting_id)
        self.assertFalse(booking.combination_id)
        self.assertEqual(booking.state, "pending")

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

    def test_no_categories_selected(self):
        """
        When no categories are selected, it should go to a special step that
        displays an error message, and allows only to go back or cancel.
        """
