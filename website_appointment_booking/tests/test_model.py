# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.resource_booking.tests.common import create_test_data


@tagged("post_install", "-at_install")
class TestResourceBookingTypeWebsite(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)

    def _new_type(self, name):
        return self.env["resource.booking.type"].create(
            {
                "name": name,
                "resource_calendar_id": self.r_calendars[2].id,
                "combination_rel_ids": [],
            }
        )

    def test_slug_auto_generated(self):
        """Slug is computed from name when not set."""
        rbt = self._new_type("30-min Consultation")
        self.assertEqual(rbt.website_slug, "30-min-consultation")

    def test_slug_not_overwritten(self):
        """Existing slug is not overwritten on name change."""
        self.rbt.website_slug = "custom-slug"
        self.rbt.name = "Changed Name"
        self.assertEqual(self.rbt.website_slug, "custom-slug")

    def test_slug_normalized_on_write(self):
        """A hand-typed slug is normalised to a URL-safe value."""
        with Form(self.rbt) as form:
            form.website_published = True
            form.website_slug = "  My Slug/With Spaces! "
        self.assertEqual(self.rbt.website_slug, "my-slug-with-spaces")

    def test_slug_unique_constraint(self):
        """Two booking types cannot share the same slug."""
        self.rbt.website_slug = "unique-slug"
        rbt2 = self._new_type("Another Type")
        with (
            self.assertRaises(IntegrityError),
            self.env.cr.savepoint(),
            mute_logger("odoo.sql_db"),
        ):
            rbt2.website_slug = "unique-slug"
            rbt2.flush_recordset()

    def test_website_published_default(self):
        """Booking types are not published by default."""
        self.assertFalse(self.rbt.is_published)
        self.assertFalse(self.rbt.website_published)

    def test_publish_requires_slug(self):
        """Publishing a type without a slug is refused."""
        rbt = self._new_type("!!!")
        self.assertFalse(rbt.website_slug)
        with self.assertRaises(ValidationError):
            rbt.is_published = True

    def test_website_url(self):
        """The mixin URL points at the public page."""
        self.rbt.website_slug = "consult"
        self.assertEqual(self.rbt.website_url, "/book/consult")

    def test_slug_special_characters(self):
        """Slug strips special characters and accents."""
        rbt = self._new_type("Réunion (30 min) & Café!")
        self.assertEqual(rbt.website_slug, "reunion-30-min-cafe")


class TestWebsiteScoping(TransactionCase):
    """A booking type bound to a website is only bookable there."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        cls.Type = cls.env["resource.booking.type"]
        cls.website = cls.env["website"].search([], limit=1)
        cls.other_website = cls.env["website"].create(
            {"name": "Other website", "domain": "https://other.test"}
        )
        cls.global_type = cls.Type.create(
            {
                "name": "Global booking",
                "resource_calendar_id": cls.r_calendars[2].id,
                "combination_rel_ids": [],
                "is_published": True,
                "website_slug": "global-booking",
            }
        )
        cls.scoped_type = cls.Type.create(
            {
                "name": "Scoped booking",
                "resource_calendar_id": cls.r_calendars[2].id,
                "combination_rel_ids": [],
                "is_published": True,
                "website_slug": "scoped-booking",
                "website_id": cls.other_website.id,
            }
        )

    def test_domain_matches_global_and_current_website(self):
        domain = self.Type._published_on_website_domain(self.website)
        found = self.Type.search(domain)
        self.assertIn(self.global_type, found)
        self.assertNotIn(self.scoped_type, found)

    def test_domain_matches_scoped_type_on_its_website(self):
        found = self.Type.search(
            self.Type._published_on_website_domain(self.other_website)
        )
        self.assertIn(self.global_type, found)
        self.assertIn(self.scoped_type, found)

    def test_unpublished_type_is_never_listed(self):
        self.global_type.is_published = False
        found = self.Type.search(
            self.Type._published_on_website_domain(self.other_website)
        )
        self.assertNotIn(self.global_type, found)
