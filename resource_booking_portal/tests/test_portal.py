# Copyright 2024 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import HttpCase


class TestCustomerPortal(HttpCase):
    def setUp(self):
        super().setUp()

        self.test_user = self.env["res.users"].create(
            {
                "name": "test user",
                "login": "test@example.com",
                "password": "password",
                "groups_id": [(4, self.env.ref("base.group_user").id)],
            }
        )

        self.resource = self.env["resource.resource"].create(
            {"name": "Test Resource", "user_id": self.test_user.id}
        )

        self.combination = self.env["resource.booking.combination"].create(
            {"resource_ids": [(6, 0, self.resource.ids)]}
        )

        self.booking_type = self.env["resource.booking.type"].create(
            {
                "name": "Test Booking Type",
                "combination_rel_ids": [(6, 0, self.combination.ids)],
            }
        )

        self.portal_user = self.env["res.users"].create(
            {
                "name": "Portal user",
                "login": "portal@example.com",
                "password": "password",
                "groups_id": [(4, self.env.ref("base.group_portal").id)],
            }
        )
        self.authenticate("portal@example.com", "password")

    def test_portal_bookings_prepare_form(self):
        response = self.url_open("/my/bookings/prepare/form")
        self.assertEqual(response.status_code, 200)

    def test_portal_bookings_create(self):
        response = self.url_open(
            "/my/bookings/create",
            data={
                "name": "Test Booking",
                "type": str(self.booking_type.id),
                "description": "Test Description",
            },
        )
        self.assertEqual(response.status_code, 200)
