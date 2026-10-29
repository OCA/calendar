# Copyright 2026 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from urllib.parse import urlencode

from odoo.tests import HttpCase, tagged


@tagged("-at_install", "post_install")
class TestCalendarSharedIcsHttp(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.feed = (
            cls.env["calendar.shared.ics"]
            .sudo()
            .create({"name": "HTTP route test feed", "active": True})
        )
        cls.other_feed = (
            cls.env["calendar.shared.ics"]
            .sudo()
            .create({"name": "Other HTTP route test feed", "active": True})
        )
        cls.feed._portal_ensure_token()
        cls.other_feed._portal_ensure_token()
        cls.token = cls.feed.access_token
        cls.other_token = cls.other_feed.access_token

    def _url(self, feed_id, endpoint="ics", token=None):
        url = f"/calendar/shared/{feed_id}/{endpoint}"
        if token is not None:
            url += "?" + urlencode({"access_token": token})
        return url

    def _fetch(self, feed_id, endpoint="ics", token=None):
        # No authenticate(): every request runs as the public user.
        return self.url_open(self._url(feed_id, endpoint, token), allow_redirects=False)

    def test_public_user_has_no_model_read_access(self):
        public_user = self.env.ref("base.public_user")
        self.assertFalse(
            self.env["calendar.shared.ics"].with_user(public_user).has_access("read")
        )

    def test_valid_ics_token(self):
        response = self._fetch(self.feed.id, token=self.token)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/calendar", response.headers.get("Content-Type", ""))
        self.assertIn(b"BEGIN:VCALENDAR", response.content)
        self.assertEqual(self.feed.access_token, self.token)

    def test_ics_rejects_missing_invalid_and_other_feed_token(self):
        for token in (None, "invalid", self.other_token):
            with self.subTest(token=token):
                self.assertEqual(
                    self._fetch(self.feed.id, token=token).status_code, 404
                )

    def test_ics_rejects_nonexistent_feed(self):
        missing_id = max(self.feed.id, self.other_feed.id) + 100000
        self.assertEqual(self._fetch(missing_id, token=self.token).status_code, 404)

    def test_landing_valid_token(self):
        response = self._fetch(self.feed.id, endpoint="landing", token=self.token)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.token.encode(), response.content)
        self.assertEqual(self.feed.access_token, self.token)

    def test_landing_rejects_missing_invalid_and_other_feed_token(self):
        for token in (None, "invalid", self.other_token):
            with self.subTest(token=token):
                self.assertEqual(
                    self._fetch(
                        self.feed.id, endpoint="landing", token=token
                    ).status_code,
                    404,
                )

    def test_inactive_feed_rejected(self):
        self.feed.active = False
        for endpoint in ("ics", "landing"):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(
                    self._fetch(
                        self.feed.id, endpoint=endpoint, token=self.token
                    ).status_code,
                    404,
                )
