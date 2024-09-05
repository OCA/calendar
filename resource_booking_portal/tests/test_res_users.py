# Copyright 2024 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestResUsers(TransactionCase):
    def setUp(self):
        super().setUp()
        self.test_user = self.env["res.users"].create(
            {
                "name": "test",
                "login": "test",
                "password": "test",
                "groups_id": [(4, self.env.ref("base.group_portal").id, 0)],
                "create_booking_from_portal": False,
            }
        )

    def test_is_portal_user(self):
        self.test_user._compute_is_portal_user()
        self.assertTrue(self.test_user.is_portal_user)

    def test_create_booking_from_portal(self):
        self.assertFalse(self.test_user.create_booking_from_portal)
        self.test_user.create_booking_from_portal = True
        self.assertTrue(self.test_user.create_booking_from_portal)
