# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import timedelta
from unittest.mock import patch

from freezegun import freeze_time

from odoo import Command, fields
from odoo.tests.common import TransactionCase

from odoo.addons.google_calendar.models.google_sync import GoogleSync
from odoo.addons.google_calendar.models.res_users import User
from odoo.addons.mail.tests.common import MailCase
from odoo.addons.resource_booking.tests.common import create_test_data

CUSTOMER_EMAIL = "customer@example.com"


@freeze_time("2021-02-26 09:00:00", tick=True)  # Last Friday of February
@patch.object(User, "_get_google_calendar_token", lambda user: "dummy-token")
class TestGoogleInvitations(TransactionCase, MailCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        cls.partner.email = CUSTOMER_EMAIL
        # Human resource of the first combination: the meeting organizer
        cls.organizer = cls.users[0]

    def setUp(self):
        super().setUp()
        # Never reach Google's API
        for method in ("_google_insert", "_google_patch", "_google_delete"):
            patcher = patch.object(GoogleSync, method, autospec=True, return_value=None)
            setattr(self, f"mock{method}", patcher.start())
            self.addCleanup(patcher.stop)

    def _connect_google(self, user, expired=True):
        """Give ``user`` a Google Calendar connection.

        By default the access token is expired, which is the normal state of
        a user who has not synchronized during the last hour.
        """
        settings = self.env["res.users.settings"]._find_or_create_for_user(user)
        delta = timedelta(hours=-1 if expired else 1)
        settings.sudo().write(
            {
                "google_calendar_rtoken": "refresh-token",
                "google_calendar_token": "access-token",
                "google_calendar_token_validity": fields.Datetime.now() + delta,
            }
        )

    def _create_booking(self, start="2021-03-01 08:00:00"):
        return self.env["resource.booking"].create(
            {
                "partner_ids": [Command.link(self.partner.id)],
                "type_id": self.rbt.id,
                "combination_id": self.rbcs[0].id,
                "combination_auto_assign": False,
                "start": start,
                # Organizer of the meeting, as website_appointment_booking does
                "user_id": self.organizer.id,
            }
        )

    def _customer_mails(self):
        return self._new_mails.filtered(
            lambda mail: mail.model == "calendar.event"
            and self.partner in mail.recipient_ids
        )

    def test_google_organizer_skips_odoo_invitations(self):
        self._connect_google(self.organizer, expired=True)
        with self.mock_mail_gateway():
            booking = self._create_booking()
        self.assertEqual(booking.state, "scheduled")
        self.assertEqual(booking.meeting_id.user_id, self.organizer)
        self.assertTrue(booking.meeting_id._google_sends_booking_invitations())
        self.assertFalse(self._customer_mails())
        # The event is pushed to Google, which invites the guests itself
        self.mock_google_insert.assert_called()
        # Rescheduling is not notified from Odoo either
        with self.mock_mail_gateway():
            booking.start = "2021-03-01 09:00:00"
        self.assertFalse(self._customer_mails())

    def test_organizer_without_google_keeps_odoo_invitations(self):
        with self.mock_mail_gateway():
            booking = self._create_booking()
        self.assertEqual(booking.state, "scheduled")
        self.assertFalse(booking.meeting_id._google_sends_booking_invitations())
        self.assertTrue(self._customer_mails())
        # Rescheduling is notified by Odoo
        with self.mock_mail_gateway():
            booking.start = "2021-03-01 09:00:00"
        self.assertTrue(self._customer_mails())

    def test_stopped_sync_keeps_odoo_invitations(self):
        self._connect_google(self.organizer, expired=False)
        self.organizer.sudo().google_synchronization_stopped = True
        with self.mock_mail_gateway():
            booking = self._create_booking()
        self.assertFalse(booking.meeting_id._google_sends_booking_invitations())
        self.assertTrue(self._customer_mails())

    def test_paused_sync_keeps_odoo_invitations(self):
        self._connect_google(self.organizer, expired=False)
        self.env["ir.config_parameter"].sudo().set_param(
            "google_calendar_sync_paused", "True"
        )
        with self.mock_mail_gateway():
            booking = self._create_booking()
        self.assertFalse(booking.meeting_id._google_sends_booking_invitations())
        self.assertTrue(self._customer_mails())

    def test_plain_meeting_not_affected(self):
        """Meetings without booking keep the ``google_calendar`` behaviour."""
        self._connect_google(self.organizer, expired=True)
        with self.mock_mail_gateway():
            meeting = self.env["calendar.event"].create(
                {
                    "name": "Plain meeting",
                    "start": "2021-03-01 08:00:00",
                    "stop": "2021-03-01 09:00:00",
                    "user_id": self.organizer.id,
                    "partner_ids": [Command.link(self.partner.id)],
                }
            )
        self.assertFalse(meeting._google_sends_booking_invitations())
        # Expired access token: core sends the mail, Google will send another
        self.assertTrue(self._customer_mails())
