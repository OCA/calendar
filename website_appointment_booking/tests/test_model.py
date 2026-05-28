# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.resource_booking.tests.common import create_test_data


@tagged("post_install", "-at_install")
class TestResourceBookingTypeWebsite(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)

    def test_slug_auto_generated(self):
        """Slug is computed from name when not set."""
        self.rbt.website_slug = False
        self.rbt.name = "30-min Consultation"
        self.rbt._compute_website_slug()
        self.assertEqual(self.rbt.website_slug, "30-min-consultation")

    def test_slug_not_overwritten(self):
        """Existing slug is not overwritten on name change."""
        self.rbt.website_slug = "custom-slug"
        self.rbt.name = "Changed Name"
        self.rbt._compute_website_slug()
        self.assertEqual(self.rbt.website_slug, "custom-slug")

    def test_slug_unique_constraint(self):
        """Two booking types cannot share the same slug."""
        self.rbt.website_slug = "unique-slug"
        rbt2 = self.env["resource.booking.type"].create(
            {
                "name": "Another Type",
                "resource_calendar_id": self.r_calendars[2].id,
                "combination_rel_ids": [],
            }
        )
        with (
            self.assertRaises(IntegrityError),
            self.env.cr.savepoint(),
            mute_logger("odoo.sql_db"),
        ):
            rbt2.website_slug = "unique-slug"
            rbt2.flush_recordset()

    def test_website_published_default(self):
        """Website published defaults to False."""
        self.assertFalse(self.rbt.website_published)

    def test_slug_special_characters(self):
        """Slug strips special characters."""
        self.rbt.website_slug = False
        self.rbt.name = "Meeting (30 min) & Coffee!"
        self.rbt._compute_website_slug()
        self.assertEqual(self.rbt.website_slug, "meeting-30-min-coffee")
