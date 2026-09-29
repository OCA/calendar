# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestViews(TransactionCase):
    """Hand-made time off is told apart through filters, not a separate menu."""

    def setUp(self):
        super().setUp()
        self.search_arch = self.env.ref(
            "resource.view_resource_calendar_leaves_search"
        ).get_combined_arch()

    def test_generated_filter_is_available(self):
        self.assertIn("filter_generated_public_holiday", self.search_arch)

    def test_unmanaged_filter_is_available(self):
        self.assertIn("filter_unmanaged_public_holiday", self.search_arch)

    def test_group_by_public_holiday_is_available(self):
        self.assertIn("group_public_holiday_line", self.search_arch)

    def test_filters_select_the_right_records(self):
        Leave = self.env["resource.calendar.leaves"]
        generated = Leave.search(
            [("resource_id", "=", False), ("public_holiday_line_id", "!=", False)]
        )
        unmanaged = Leave.search(
            [("resource_id", "=", False), ("public_holiday_line_id", "=", False)]
        )
        self.assertFalse(generated & unmanaged, "the two filters must not overlap")
