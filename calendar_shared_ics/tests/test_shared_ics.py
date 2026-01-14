# Copyright 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from datetime import timedelta
from unittest.mock import patch

import vobject

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestCalendarSharedIcsFullNoHttp(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Shared = self.env["calendar.shared.ics"]
        self.Users = self.env["res.users"]
        self.Partners = self.env["res.partner"]
        self.Event = self.env["calendar.event"]
        self.group_user = self.env.ref("base.group_user")
        self.group_manager = self.env.ref(
            "calendar_shared_ics.group_calendar_shared_ics_manager"
        )
        self.marker = f"[ICS{self.__class__.__name__}]"
        # Partners
        self.partner_mgr = self.Partners.create({"name": f"{self.marker} Mgr Partner"})
        self.partner_u1 = self.Partners.create({"name": f"{self.marker} U1 Partner"})
        self.partner_u2 = self.Partners.create({"name": f"{self.marker} U2 Partner"})
        # Users
        self.user_mgr = self.Users.create(
            {
                "name": f"{self.marker} Manager",
                "login": "ics_nohttp_manager",
                "password": "ics_nohttp_manager",
                "partner_id": self.partner_mgr.id,
                "groups_id": [(6, 0, [self.group_user.id, self.group_manager.id])],
            }
        )
        self.user_u1 = self.Users.create(
            {
                "name": f"{self.marker} User1",
                "login": "ics_nohttp_user1",
                "password": "ics_nohttp_user1",
                "partner_id": self.partner_u1.id,
                "groups_id": [(6, 0, [self.group_user.id])],
            }
        )
        self.user_u2 = self.Users.create(
            {
                "name": f"{self.marker} User2",
                "login": "ics_nohttp_user2",
                "password": "ics_nohttp_user2",
                "partner_id": self.partner_u2.id,
                "groups_id": [(6, 0, [self.group_user.id])],
            }
        )
        # Feeds
        self.feed_u1 = self.Shared.sudo().create(
            {
                "name": f"{self.marker} Feed U1",
                "partner_id": self.partner_u1.id,
                "active": True,
            }
        )
        self.feed_u2 = self.Shared.sudo().create(
            {
                "name": f"{self.marker} Feed U2",
                "partner_id": self.partner_u2.id,
                "active": True,
            }
        )
        self.feed_u1.sudo()._portal_ensure_token()
        self.feed_u2.sudo()._portal_ensure_token()
        # Events
        now = fields.Datetime.now()
        self.event_u1 = self.Event.sudo().create(
            {
                "name": f"{self.marker} Event U1",
                "start": now,
                "stop": now,
                "partner_ids": [(6, 0, [self.partner_u1.id])],
            }
        )
        self.event_u2 = self.Event.sudo().create(
            {
                "name": f"{self.marker} Event U2",
                "start": now,
                "stop": now,
                "partner_ids": [(6, 0, [self.partner_u2.id])],
            }
        )

    def test_manager_can_read_all_feeds(self):
        feeds = self.Shared.with_user(self.user_mgr).search([])
        self.assertIn(self.feed_u1, feeds)
        self.assertIn(self.feed_u2, feeds)

    def test_user_can_only_read_own_feed(self):
        feeds_u1 = self.Shared.with_user(self.user_u1).search([])
        self.assertIn(self.feed_u1, feeds_u1)
        self.assertNotIn(self.feed_u2, feeds_u1)

        self.Shared.with_user(self.user_u1).browse(self.feed_u1.id).read(["name"])
        with self.assertRaises(AccessError):
            self.Shared.with_user(self.user_u1).browse(self.feed_u2.id).read(["name"])

    def test_check_access_token(self):
        token = self.feed_u1.sudo().access_token
        self.assertTrue(self.feed_u1.sudo()._check_access_token(token))
        self.assertFalse(self.feed_u1.sudo()._check_access_token("WRONG"))
        self.assertFalse(self.feed_u1.sudo()._check_access_token(False))

    def test_get_share_url_points_to_landing(self):
        # _get_share_url should return a relative URL to the public landing page
        self.feed_u1.sudo()._portal_ensure_token()
        token = self.feed_u1.sudo().access_token
        url = self.feed_u1.sudo()._get_share_url()
        self.assertIn(f"/calendar/shared/{self.feed_u1.id}/landing", url)
        self.assertIn("access_token=", url)
        self.assertIn(token, url)

    def test_computed_subscription_urls(self):
        # These should be absolute and contain /ics + access_token
        self.feed_u1.sudo()._portal_ensure_token()
        token = self.feed_u1.sudo().access_token
        share_url = self.feed_u1.sudo().share_url
        webcal_url = self.feed_u1.sudo().share_webcal_url
        self.assertTrue(share_url)
        self.assertTrue(webcal_url)
        self.assertIn(f"/calendar/shared/{self.feed_u1.id}/ics", share_url)
        self.assertIn(f"access_token={token}", share_url)
        self.assertIn(f"/calendar/shared/{self.feed_u1.id}/ics", webcal_url)
        self.assertIn(f"access_token={token}", webcal_url)
        self.assertTrue(webcal_url.startswith("webcal://"))

    def test_domain_partner_filter(self):
        dom = self.feed_u1.sudo()._get_events_domain()
        self.assertIn(("partner_ids", "in", [self.partner_u1.id]), dom)
        events = self.feed_u1.sudo()._get_events_for_export()
        self.assertIn(self.event_u1, events)
        self.assertNotIn(self.event_u2, events)

    def test_domain_extra_filter(self):
        # exclude U1 event by name
        self.feed_u1.sudo().domain = "[('name', '!=', '%s')]" % (
            f"{self.marker} Event U1"
        )
        events = self.feed_u1.sudo()._get_events_for_export()
        self.assertNotIn(self.event_u1, events)

    def test_domain_invalid_raises(self):
        self.feed_u1.sudo().domain = "THIS_IS_NOT_A_DOMAIN"
        with self.assertRaises(ValueError):
            self.feed_u1.sudo()._get_events_domain()

    def test_render_ics_content_contains_expected(self):
        events = self.feed_u1.sudo()._get_events_for_export()
        # Make sure we’re only exporting U1 event in this feed
        self.assertEqual(events, self.event_u1)

        ics_u1 = (
            b"BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nSUMMARY:%s\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
            % ((f"{self.marker} Event U1").encode("utf-8"))
        )
        with patch.object(
            type(events), "_get_ics_file", return_value={self.event_u1.id: ics_u1}
        ):
            out = self.feed_u1.sudo()._render_ics_content()
            text = out.decode("utf-8", errors="replace")
            self.assertIn("BEGIN:VCALENDAR", text)
            self.assertIn(f"{self.marker} Event U1", text)
            self.assertIn("END:VCALENDAR", text)

    def test_rrule_dtstart(self):
        events = self.feed_u1.sudo()._get_events_for_export()
        self.assertEqual(events, self.event_u1)

        malformed = (
            b"BEGIN:VCALENDAR\r\n"
            b"VERSION:2.0\r\n"
            b"PRODID:-//TEST//EN\r\n"
            b"BEGIN:VEVENT\r\n"
            b"UID:test-uid-1\r\n"
            b"RRULE:DTSTART:20220425T063000\r\n"
            b"RRULE:FREQ=WEEKLY;UNTIL=20220704T235959;BYDAY=MO\r\n"
            b"SUMMARY:Recurrent Test\r\n"
            b"END:VEVENT\r\n"
            b"END:VCALENDAR\r\n"
        )
        with patch.object(
            type(events), "_get_ics_file", return_value={self.event_u1.id: malformed}
        ):
            out = self.feed_u1.sudo()._render_ics_content()
        text = out.decode("utf-8", errors="replace")
        # The malformed line must be gone
        self.assertNotIn("RRULE:DTSTART:", text)
        # RRULE should remain present
        self.assertIn("RRULE:FREQ=WEEKLY;UNTIL=20220704T235959;BYDAY=MO", text)
        # Ensure the output is valid VCALENDAR and VEVENT has dtstart + rrule
        cal = vobject.readOne(text)
        self.assertTrue(getattr(cal, "vevent_list", None))
        ve = cal.vevent_list[0]
        self.assertTrue(hasattr(ve, "rrule"))
        self.assertIn("FREQ=WEEKLY", ve.rrule.value)

    def test_rrule_dtstart_dropped(self):
        events = self.feed_u1.sudo()._get_events_for_export()
        self.assertEqual(events, self.event_u1)
        malformed_with_dtstart = (
            b"BEGIN:VCALENDAR\r\n"
            b"VERSION:2.0\r\n"
            b"PRODID:-//TEST//EN\r\n"
            b"BEGIN:VEVENT\r\n"
            b"UID:test-uid-2\r\n"
            b"DTSTART:20220425T063000\r\n"
            b"RRULE:DTSTART:20220425T063000\r\n"
            b"RRULE:FREQ=WEEKLY;UNTIL=20220704T235959;BYDAY=MO\r\n"
            b"SUMMARY:Recurrent Test 2\r\n"
            b"END:VEVENT\r\n"
            b"END:VCALENDAR\r\n"
        )
        with patch.object(
            type(events),
            "_get_ics_file",
            return_value={self.event_u1.id: malformed_with_dtstart},
        ):
            out = self.feed_u1.sudo()._render_ics_content()
        text = out.decode("utf-8", errors="replace")
        # Malformed line removed
        self.assertNotIn("RRULE:DTSTART:", text)
        # DTSTART should remain, but only once (no duplicates)
        self.assertEqual(text.count("DTSTART:20220425T063000"), 1)

    def test_only_recent_events(self):
        # Create an old event (ended 10 days ago)
        old_stop = fields.Datetime.now() - timedelta(days=10)
        old_start = old_stop
        old_event = self.Event.sudo().create(
            {
                "name": f"{self.marker} Old Event U1",
                "start": old_start,
                "stop": old_stop,
                "partner_ids": [(6, 0, [self.partner_u1.id])],
            }
        )
        # Default is only_recent_events=True and recent_days=7
        self.feed_u1.sudo().only_recent_events = True
        self.feed_u1.sudo().recent_days = 7
        events = self.feed_u1.sudo()._get_events_for_export()
        self.assertIn(self.event_u1, events)
        self.assertNotIn(old_event, events)

    def test_not_only_recent_events(self):
        old_stop = fields.Datetime.now() - timedelta(days=10)
        old_start = old_stop
        old_event = self.Event.sudo().create(
            {
                "name": f"{self.marker} Old Event U1 2",
                "start": old_start,
                "stop": old_stop,
                "partner_ids": [(6, 0, [self.partner_u1.id])],
            }
        )
        self.feed_u1.sudo().only_recent_events = False
        events = self.feed_u1.sudo()._get_events_for_export()
        self.assertIn(self.event_u1, events)
        self.assertIn(old_event, events)

    def test_reset_access_token(self):
        feed = self.feed_u1
        old_token = feed.sudo().access_token
        self.assertTrue(old_token)
        # Regular user must NOT be able to rotate token
        with self.assertRaises(AccessError):
            feed.with_user(self.user_u1).action_reset_access_token()
        feed_refreshed = self.Shared.sudo().browse(feed.id)
        self.assertEqual(feed_refreshed.access_token, old_token)
        # Manager should be allowed to rotate
        feed.with_user(self.user_mgr).action_reset_access_token()
        feed_refreshed2 = self.Shared.sudo().browse(feed.id)
        self.assertTrue(feed_refreshed2.access_token)
        self.assertNotEqual(feed_refreshed2.access_token, old_token)
