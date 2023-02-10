# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from freezegun import freeze_time

from odoo.exceptions import ValidationError
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

    def _set_wizard_categories(self, wizard, resource_categories):
        wizard.resource_category_ids = [(6, 0, [r.id for r in resource_categories])]

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

    def _get_selected_resources_on_current_step(self, wizard):
        return wizard.current_resource_booking_category_selection_id.mapped(
            "resource_ids.resource_id"
        )

    def _select_resources_by_index_on_current_step(self, wizard, indexes):
        available_resources = self._get_available_resources_on_current_step(wizard)
        wizard.current_selected_resource_ids = [
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
        self.assertEqual(booking.state, "pending")
        wizard = self._create_wizard_with_selected_categories(
            booking, [self.room_category, self.worker_category]
        )
        wizard.open_next()
        self.assertEqual(
            wizard.configure_step_message,
            "Select resources for category room:",
        )
        self._select_resources_by_index_on_current_step(wizard, [0])
        wizard.open_next()
        self._select_resources_by_index_on_current_step(wizard, [0])
        wizard.open_next()
        wizard.create_combination()
        self.assertEqual(booking.state, "scheduled")
        resources = booking.combination_id.resource_ids
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
        self.assertEqual(booking.combination_id, existing_combination)

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

    def test_configure_step_order(self):
        """
        The configuration steps should propose each resource category in
        alphabetical order.
        """
        test_category = self.env["resource.category"].create({"name": "test"})
        booking = self._create_resource_booking()
        # it should be independent of the creation order
        wizard = self._create_wizard_with_selected_categories(
            booking, [self.worker_category, test_category, self.room_category]
        )
        wizard.open_next()
        self.assertEqual(
            wizard.current_resource_booking_category_selection_id.resource_category_id.name,
            "room",
        )
        wizard.open_next()
        self.assertEqual(
            wizard.current_resource_booking_category_selection_id.resource_category_id.name,
            "test",
        )
        wizard.open_next()
        self.assertEqual(
            wizard.current_resource_booking_category_selection_id.resource_category_id.name,
            "worker",
        )

    def test_available_resources_order(self):
        """
        The available resources in each step should be in alphabetical order.
        """
        a_test_resource = self.env["resource.resource"].create(
            {
                "name": "a test room",
                "resource_type": "material",
                "calendar_id": self.full_calendar.id,
                "resource_category_ids": [(6, 0, [self.room_category.id])],
            }
        )
        booking = self._create_resource_booking()
        wizard = self._create_wizard_with_selected_categories(
            booking, [self.room_category]
        )
        wizard.open_next()
        available_resources = self._get_available_resources_on_current_step(wizard)
        self.assertEqual(available_resources[0].resource_id, a_test_resource)

    def test_no_available_resources_found(self):
        """
        If no matching available resources are found, no resource combination
        should be created nor assigned to the booking.
        """
        category = self.env["resource.category"].create({"name": "test"})
        booking = self._create_resource_booking()
        wizard = self._create_wizard_with_selected_categories(booking, [category])
        wizard.open_next()
        self.assertEqual(
            wizard.configure_step_message,
            "No available resources found for category test.",
        )
        wizard.open_next()
        wizard.create_combination()
        self.assertFalse(booking.combination_id)
        self.assertEqual(booking.state, "pending")

    def test_re_select_current_combination(self):
        """
        When changing the resource combination of a booking, the currently
        assigned resources should be considered as available for the booking.
        """
        existing_combination = self._create_resource_combination(
            [self.room_1, self.worker_1]
        )
        self._add_combination_to_booking_type(self.booking_type_1, existing_combination)
        booking = self._create_resource_booking()
        booking.combination_id = existing_combination
        wizard = self._create_wizard_with_selected_categories(
            booking, [self.room_category, self.worker_category]
        )
        wizard.open_next()
        self._select_resources_by_index_on_current_step(wizard, [0])
        wizard.open_next()
        self._select_resources_by_index_on_current_step(wizard, [0])
        wizard.open_next()
        wizard.create_combination()
        self.assertEqual(booking.combination_id, existing_combination)

    def test_select_resource_in_multiple_selected_categories(self):
        """
        When a resource matches several selected resource categories, it
        should appear several times in the list of available resources, but
        selecting it for one category should make it unavailable for the
        others.
        """
        test_category = self.env["resource.category"].create(
            {
                "name": "test",
                "resource_ids": [
                    (6, 0, [self.worker_1.id, self.worker_2.id]),
                ],
            }
        )
        booking = self._create_resource_booking()
        wizard = self._create_wizard_with_selected_categories(
            booking, [test_category, self.worker_category]
        )
        wizard.open_next()
        available_resources = self._get_available_resources_on_current_step(wizard)
        self.assertEqual(len(available_resources), 2)
        self._select_resources_by_index_on_current_step(wizard, [0])
        wizard.open_next()
        available_resources = self._get_available_resources_on_current_step(wizard)
        self.assertEqual(len(available_resources), 1)
        self.assertEqual(available_resources[0].resource_id, self.worker_2)
        self._select_resources_by_index_on_current_step(wizard, [0])
        wizard.open_previous()
        available_resources = self._get_available_resources_on_current_step(wizard)
        self.assertEqual(len(available_resources), 1)

    def test_keep_selection_across_steps(self):
        """
        Going forward and back in the wizard should not affect the selections
        made on any step.
        """
        booking = self._create_resource_booking()
        wizard = self._create_wizard_with_selected_categories(
            booking, [self.room_category, self.worker_category]
        )
        self.assertEqual(wizard.configure_step_count, 2)
        wizard.open_next()
        self._select_resources_by_index_on_current_step(wizard, [0])
        wizard.open_next()
        self._select_resources_by_index_on_current_step(wizard, [1])
        wizard.open_previous()
        selected_resources = self._get_selected_resources_on_current_step(wizard)
        self.assertEqual(selected_resources, self.room_1)
        wizard.open_next()
        selected_resources = self._get_selected_resources_on_current_step(wizard)
        self.assertEqual(selected_resources, self.worker_2)
        wizard.open_previous()
        wizard.open_previous()
        self._set_wizard_categories(wizard, [self.worker_category])
        self.assertEqual(wizard.configure_step_count, 1)
        wizard.open_next()
        selected_resources = self._get_selected_resources_on_current_step(wizard)
        self.assertEqual(selected_resources, self.worker_2)

    def test_no_dates(self):
        """
        Opening the wizard if the start date or the duration is not set should
        raise a validation error.
        """
        booking = self.env["resource.booking"].create(
            {
                "partner_id": self.partner_1.id,
                "type_id": self.booking_type_1.id,
                # no start and no duration
            }
        )
        with self.assertRaises(ValidationError) as cm:
            self._create_wizard_with_selected_categories(
                booking, [self.room_category, self.worker_category]
            )
        self.assertEqual(
            str(cm.exception),
            "To select resources, the booking must have a start date and a "
            "duration.",
        )
        booking = self.env["resource.booking"].create(
            {
                "partner_id": self.partner_1.id,
                "type_id": self.booking_type_1.id,
                # no start
                "duration": 2,
            }
        )
        with self.assertRaises(ValidationError) as cm:
            self._create_wizard_with_selected_categories(
                booking, [self.room_category, self.worker_category]
            )
        booking = self.env["resource.booking"].create(
            {
                "partner_id": self.partner_1.id,
                "type_id": self.booking_type_1.id,
                "start": "2023-02-06 10:00:00",
                # no duration
            }
        )
        # this does not fail because a default duration is taken from the
        # booking type.
        self._create_wizard_with_selected_categories(
            booking, [self.room_category, self.worker_category]
        )
        # if this default duration is set to 0.
        self.booking_type_1.duration = 0
        booking = self.env["resource.booking"].create(
            {
                "partner_id": self.partner_1.id,
                "type_id": self.booking_type_1.id,
                "start": "2023-02-06 10:00:00",
                # no duration
            }
        )
        with self.assertRaises(ValidationError) as cm:
            self._create_wizard_with_selected_categories(
                booking, [self.room_category, self.worker_category]
            )

    def test_no_categories_selected(self):
        """
        When no categories are selected, it should go to a special step that
        displays an error message, and allows only to go back or cancel.
        """
        booking = self._create_resource_booking()
        wizard = self._create_wizard_with_selected_categories(booking, [])
        # currently, we leave it like it is: there is simply no configuration
        # steps. this allows to easily all resources.
        self.assertEqual(wizard.configure_step_count, 0)
        wizard.open_next()
        wizard.create_combination()
        self.assertFalse(booking.combination_id)
        self.assertEqual(booking.state, "pending")

    def test_no_resources_selected(self):
        """
        When no resources are selected, no resource combination should be
        assigned.
        """
        booking = self._create_resource_booking()
        wizard = self._create_wizard_with_selected_categories(
            booking, [self.room_category, self.worker_category]
        )
        wizard.open_next()
        wizard.open_next()
        wizard.open_next()
        wizard.create_combination()
        self.assertFalse(booking.combination_id)
        self.assertEqual(booking.state, "pending")

    def test_unassign_resources(self):
        """
        On a booking with a resource combination, re-opening the wizard and
        selecting no resources should unassign the resource combination.
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
        self.assertEqual(booking.state, "scheduled")
        wizard = self._create_wizard_with_selected_categories(
            booking, [self.room_category]
        )
        wizard.open_next()
        wizard.open_next()
        wizard.create_combination()
        self.assertFalse(booking.combination_id)
        self.assertEqual(booking.state, "pending")

    def test_change_selected_resource_categories(self):
        """
        Going back to the first step and unselecting a previously selected
        category should update the next steps accordingly.
        """
        booking = self._create_resource_booking()
        wizard = self._create_wizard_with_selected_categories(
            booking, [self.room_category, self.worker_category]
        )
        wizard.open_next()
        self.assertEqual(wizard.configure_step_count, 2)
        wizard.open_previous()
        # unselect the first category.
        wizard.resource_category_ids = [(3, self.room_category.id, 0)]
        wizard.open_next()
        self.assertEqual(wizard.configure_step_count, 1)
