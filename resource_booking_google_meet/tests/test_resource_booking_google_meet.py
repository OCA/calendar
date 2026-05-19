# Copyright 2026 Ledo Enterprises - D. Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestResourceBookingGoogleMeet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.booking_type = cls.env["resource.booking.type"].create(
            {
                "name": "Test Booking Type",
                "location": "123 Main St",
            }
        )

    def test_prepare_meeting_vals_clears_location_when_no_videocall(self):
        """location is cleared so google_calendar adds conferencing."""
        booking = self.env["resource.booking"].create(
            {
                "type_id": self.booking_type.id,
                "partner_ids": [(4, self.env.ref("base.partner_demo").id)],
            }
        )
        vals = booking._prepare_meeting_vals()
        self.assertFalse(
            vals.get("location"),
            "location must be falsy so google_calendar requests a Meet URL",
        )

    def test_prepare_meeting_vals_preserves_videocall_location(self):
        """Static videocall_location (e.g. Zoom) is left unchanged."""
        self.booking_type.videocall_location = "https://zoom.us/j/123456"
        booking = self.env["resource.booking"].create(
            {
                "type_id": self.booking_type.id,
                "partner_ids": [(4, self.env.ref("base.partner_demo").id)],
            }
        )
        vals = booking._prepare_meeting_vals()
        self.assertEqual(
            vals.get("videocall_location"),
            "https://zoom.us/j/123456",
            "Static videocall_location must be preserved",
        )
