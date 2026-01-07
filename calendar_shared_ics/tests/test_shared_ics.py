# Copyright 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from unittest.mock import patch

from odoo import Command, fields
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
        self.marker = f"[ICS_NOHTTP_{self.__class__.__name__}]"
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
                "groups_id": [Command.set([self.group_user.id, self.group_manager.id])],
            }
        )
        self.user_u1 = self.Users.create(
            {
                "name": f"{self.marker} User1",
                "login": "ics_nohttp_user1",
                "password": "ics_nohttp_user1",
                "partner_id": self.partner_u1.id,
                "groups_id": [Command.set([self.group_user.id])],
            }
        )
        self.user_u2 = self.Users.create(
            {
                "name": f"{self.marker} User2",
                "login": "ics_nohttp_user2",
                "password": "ics_nohttp_user2",
                "partner_id": self.partner_u2.id,
                "groups_id": [Command.set([self.group_user.id])],
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

        # Events (real records to test domain/search)
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

        # Patch _get_ics_file on the recordset model class
        with patch.object(
            type(events), "_get_ics_file", return_value={self.event_u1.id: ics_u1}
        ):
            out = self.feed_u1.sudo()._render_ics_content()
            text = out.decode("utf-8", errors="replace")
            self.assertIn("BEGIN:VCALENDAR", text)
            self.assertIn(f"{self.marker} Event U1", text)
            self.assertIn("END:VCALENDAR", text)
