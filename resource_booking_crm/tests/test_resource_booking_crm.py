# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import MagicMock, patch

from freezegun import freeze_time

from odoo import Command
from odoo.tests import Form, new_test_user
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.resource_booking.tests.common import create_test_data


@freeze_time("2021-02-26 09:00:00", tick=True)
class TestResourceBookingCrm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        # Models
        cls.Booking = cls.env["resource.booking"]
        cls.Lead = cls.env["crm.lead"]
        # Instances
        cls.team = cls.env["crm.team"].create({"name": "Booking team"})
        cls.salesperson = new_test_user(
            cls.env,
            login="rb_crm_salesman",
            groups="sales_team.group_sale_salesman,resource_booking.group_user",
        )
        cls.tag = cls.env["crm.tag"].create({"name": "From booking"})
        cls.company_partner = cls.env["res.partner"].create(
            {"name": "Customer Inc", "is_company": True}
        )
        cls.partner.write(
            {"parent_id": cls.company_partner.id, "email": "customer@example.com"}
        )
        cls.campaign = cls.env["utm.campaign"].create({"name": "Spring demo"})
        cls.source = cls.env["utm.source"].create({"name": "Newsletter"})
        cls.medium = cls.env["utm.medium"].create({"name": "Email"})
        with Form(cls.rbt) as type_form:
            type_form.crm_lead_type = "opportunity"
            type_form.crm_team_id = cls.team
            type_form.crm_user_id = cls.salesperson
            type_form.crm_tag_ids.add(cls.tag)

    def _create_booking(self, **vals):
        return self.Booking.create(
            {
                "partner_ids": [Command.set(self.partner.ids)],
                "type_id": self.rbt.id,
                **vals,
            }
        )

    def test_disabled_type_creates_no_lead(self):
        self.rbt.crm_lead_type = False
        booking = self._create_booking(start="2021-03-01 08:00:00")
        self.assertTrue(booking.meeting_id)
        self.assertFalse(booking.lead_id)

    def test_scheduled_booking_creates_opportunity(self):
        booking = self._create_booking(start="2021-03-01 08:00:00")
        lead = booking.lead_id
        self.assertTrue(lead)
        self.assertEqual(lead.type, "opportunity")
        self.assertEqual(lead.partner_id, self.partner)
        self.assertEqual(lead.email_from, "customer@example.com")
        self.assertEqual(lead.team_id, self.team)
        self.assertEqual(lead.user_id, self.salesperson)
        self.assertEqual(lead.tag_ids, self.tag)
        self.assertEqual(lead.resource_booking_ids, booking)
        self.assertEqual(lead.resource_booking_count, 1)
        self.assertEqual(booking.meeting_id.opportunity_id, lead)
        action = lead.action_view_resource_bookings()
        self.assertEqual(self.Booking.search(action["domain"]), booking)
        self.assertEqual(booking.action_view_crm_lead()["res_id"], lead.id)

    def test_lead_type_and_salesperson_fallback(self):
        self.rbt.write({"crm_lead_type": "lead", "crm_user_id": False})
        booking = self._create_booking(
            start="2021-03-01 08:00:00", user_id=self.salesperson.id
        )
        self.assertEqual(booking.lead_id.type, "lead")
        self.assertEqual(booking.lead_id.user_id, self.salesperson)

    def test_pending_booking_creates_lead_when_scheduled(self):
        booking = self._create_booking()
        self.assertEqual(booking.state, "pending")
        self.assertFalse(booking.lead_id)
        booking.start = "2021-03-01 08:00:00"
        lead = booking.lead_id
        self.assertTrue(lead)
        booking.start = "2021-03-01 10:00:00"
        self.assertEqual(booking.lead_id, lead)
        booking.action_unschedule()
        booking.start = "2021-03-08 08:00:00"
        self.assertEqual(booking.lead_id, lead)
        self.assertEqual(
            self.Lead.search_count([("partner_id", "=", self.partner.id)]), 1
        )

    def test_schedule_from_calendar_creates_lead(self):
        booking = self._create_booking()
        action = booking.action_schedule()
        self.env[action["res_model"]].with_context(**action["context"]).create(
            {"start": "2021-03-01 08:00:00", "stop": "2021-03-01 08:30:00"}
        )
        self.assertTrue(booking.meeting_id)
        self.assertTrue(booking.lead_id)

    def test_backend_form_creates_lead(self):
        booking_form = Form(self.Booking.with_context(default_type_id=self.rbt.id))
        booking_form.partner_ids.add(self.partner)
        booking_form.start = "2021-03-01 08:00:00"
        booking = booking_form.save()
        self.assertTrue(booking.lead_id)

    def test_utm_copied_to_lead(self):
        booking = self._create_booking(
            start="2021-03-01 08:00:00",
            campaign_id=self.campaign.id,
            source_id=self.source.id,
            medium_id=self.medium.id,
        )
        lead = booking.lead_id
        self.assertEqual(lead.campaign_id, self.campaign)
        self.assertEqual(lead.source_id, self.source)
        self.assertEqual(lead.medium_id, self.medium)

    @mute_logger("odoo.addons.mail.models.mail_mail")
    def test_utm_cookies_captured_on_public_booking(self):
        """The public booking page creates bookings with sudo in the
        visitor's request: the UTM cookies end on the booking and its lead."""
        fake_request = MagicMock()
        fake_request.cookies = {
            "odoo_utm_campaign": "Autumn webinar",
            "odoo_utm_source": "LinkedIn",
            "odoo_utm_medium": "Social",
        }
        public_user = self.env.ref("base.public_user")
        with patch("odoo.addons.utm.models.utm_mixin.request", fake_request):
            booking = (
                self.Booking.with_user(public_user)
                .sudo()
                .create(
                    {
                        "partner_ids": [Command.set(self.partner.ids)],
                        "type_id": self.rbt.id,
                        "user_id": False,
                    }
                )
            )
        booking.start = "2021-03-01 08:00:00"
        self.assertEqual(booking.campaign_id.name, "Autumn webinar")
        self.assertEqual(booking.source_id.name, "LinkedIn")
        self.assertEqual(booking.medium_id.name, "Social")
        lead = booking.lead_id
        self.assertEqual(lead.campaign_id, booking.campaign_id)
        self.assertEqual(lead.source_id, booking.source_id)
        self.assertEqual(lead.medium_id, booking.medium_id)

    def test_salesman_cookies_ignored(self):
        fake_request = MagicMock()
        fake_request.cookies = {"odoo_utm_campaign": "Ignored"}
        with patch("odoo.addons.utm.models.utm_mixin.request", fake_request):
            booking = self.Booking.with_user(self.salesperson).create(
                {
                    "partner_ids": [
                        Command.set((self.partner | self.salesperson.partner_id).ids)
                    ],
                    "type_id": self.rbt.id,
                }
            )
        self.assertFalse(booking.campaign_id)

    def test_reuse_open_lead(self):
        self.rbt.crm_lead_reuse = True
        contact = self.env["res.partner"].create(
            {"name": "Colleague", "parent_id": self.company_partner.id}
        )
        open_lead = self.Lead.create(
            {"name": "Existing deal", "partner_id": contact.id}
        )
        booking = self._create_booking(start="2021-03-01 08:00:00")
        self.assertEqual(booking.lead_id, open_lead)
        self.assertEqual(open_lead.resource_booking_ids, booking)

    def test_reuse_skips_won_and_archived_leads(self):
        self.rbt.crm_lead_reuse = True
        won_lead = self.Lead.create({"name": "Won deal", "partner_id": self.partner.id})
        won_lead.action_set_won()
        lost_lead = self.Lead.create(
            {"name": "Lost deal", "partner_id": self.partner.id}
        )
        lost_lead.action_archive()
        booking = self._create_booking(start="2021-03-01 08:00:00")
        self.assertTrue(booking.lead_id)
        self.assertNotIn(booking.lead_id, won_lead | lost_lead)

    def test_booking_user_without_crm_rights(self):
        booking_user = new_test_user(
            self.env,
            login="rb_only_user",
            groups="base.group_user,resource_booking.group_user",
        )
        booking = self._create_booking(
            partner_ids=[Command.set((self.partner | booking_user.partner_id).ids)],
        )
        booking.with_user(booking_user).start = "2021-03-01 08:00:00"
        self.assertTrue(booking.lead_id)
        portal_user = new_test_user(
            self.env, login="rb_portal_user", groups="base.group_portal"
        )
        booking2 = self._create_booking(
            partner_ids=[Command.set(portal_user.partner_id.ids)]
        )
        booking2.with_user(portal_user).sudo().with_context(
            using_portal=True
        ).start = "2021-03-02 08:00:00"
        self.assertTrue(booking2.lead_id)
        self.assertEqual(booking2.lead_id.partner_id, portal_user.partner_id)
