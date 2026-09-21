# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from datetime import datetime

from freezegun import freeze_time
from lxml.html import fromstring

from odoo.tests import tagged
from odoo.tests.common import HttpCase

from odoo.addons.resource_booking.tests.common import create_test_data

# The shared fixture (resource_booking.tests.common) has UTC calendars with
# Monday and Tuesday attendances from 08:00 to 17:00, 30-minute slots and a
# 24-hour modification deadline. Time is frozen on Friday 2021-02-26, so
# Monday 2021-03-01 is the first bookable day.


@freeze_time("2021-02-26 09:00:00", tick=True)
@tagged("post_install", "-at_install")
class TestWebsiteAppointmentBooking(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        cls.rbt.write(
            {
                "is_published": True,
                "website_slug": "test-booking",
            }
        )

    def _url_xml(self, url, data=None, timeout=10):
        """Open a URL and return its parsed lxml tree."""
        response = self.url_open(url, data, timeout=timeout)
        return fromstring(response.content)

    def _get_csrf_token(self, page):
        """Extract CSRF token from a page's hidden input."""
        inputs = page.cssselect('input[name="csrf_token"]')
        if inputs:
            return inputs[0].get("value")
        return ""

    def _confirm(self, data, slug="test-booking"):
        """POST the confirm form with a fresh CSRF token."""
        page = self._url_xml(f"/book/{slug}/2021/3")
        data = dict(data, csrf_token=self._get_csrf_token(page))
        return self.url_open(f"/book/{slug}/confirm", data=data, timeout=30)

    def _booking_for(self, email):
        return self.env["resource.booking"].search(
            [("type_id", "=", self.rbt.id), ("partner_ids.email", "=", email)]
        )

    def test_unpublished_returns_404(self):
        """Unpublished booking types are not accessible.

        Uses a slug that has never been published, since changes made in test
        methods are not visible to the HTTP server thread in HttpCase.
        """
        response = self.url_open("/book/unpublished-type")
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_slug_returns_404(self):
        """Unknown slugs return 404."""
        response = self.url_open("/book/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_booking_page_renders(self):
        """Published booking page renders with calendar."""
        page = self._url_xml("/book/test-booking")
        self.assertTrue(
            page.cssselect(".o_wab_title:contains('Test resource booking type')")
        )
        self.assertTrue(page.cssselect(".o_wab_meta_pill:contains('30 min')"))

    def test_booking_page_february_no_slots(self):
        """February 2021 has no available Monday/Tuesday slots (too close)."""
        page = self._url_xml("/book/test-booking")
        self.assertTrue(
            page.cssselect(".o_wab_empty_month:contains('No available slots')")
        )

    def test_booking_page_march_has_slots(self):
        """March 2021 should have available slots on Mondays and Tuesdays."""
        page = self._url_xml("/book/test-booking/2021/3")
        self.assertTrue(page.cssselect(".o_wab_month_label:contains('March 2021')"))
        self.assertTrue(page.cssselect("#o_wab_slot_data"))
        self.assertTrue(page.cssselect(".o_wab_table"))

    def test_booking_page_navigation(self):
        """Month navigation links work."""
        page = self._url_xml("/book/test-booking/2021/3")
        self.assertTrue(page.cssselect('a[href*="/book/test-booking/2021/4"]'))

    def test_booking_form_has_guard_fields(self):
        """The confirm form ships the honeypot and reCAPTCHA inputs."""
        page = self._url_xml("/book/test-booking/2021/3")
        self.assertTrue(page.cssselect("#o_wab_form .o_wab_hp input[name]"))
        self.assertTrue(
            page.cssselect("#o_wab_form input[name='recaptcha_token_response']")
        )

    def test_confirm_creates_booking(self):
        """Successful form submission creates a confirmed booking."""
        response = self._confirm(
            {
                "name": "Test Visitor",
                "email": "visitor@example.com",
                "when": "2021-03-01T10:00:00+00:00",
            }
        )
        self.assertIn("/book/test-booking/success", response.url)
        booking = self._booking_for("visitor@example.com")
        self.assertTrue(booking)
        self.assertEqual(booking.state, "confirmed")
        self.assertTrue(booking.meeting_id)
        partner = self.env["res.partner"].search(
            [("email", "=ilike", "visitor@example.com")]
        )
        self.assertTrue(partner)
        self.assertEqual(partner.name, "Test Visitor")

    def test_confirm_organizer_is_not_public_user(self):
        """The meeting organizer is the assigned human resource."""
        self._confirm(
            {
                "name": "Organizer Check",
                "email": "organizer@example.com",
                "when": "2021-03-01T11:00:00+00:00",
            }
        )
        booking = self._booking_for("organizer@example.com")
        self.assertTrue(booking)
        public_user = self.env.ref("base.public_user")
        self.assertTrue(booking.user_id)
        self.assertNotEqual(booking.user_id, public_user)
        self.assertEqual(booking.meeting_id.user_id, booking.user_id)
        self.assertIn(
            booking.user_id,
            booking.combination_id.resource_ids.user_id,
        )

    def test_confirm_missing_fields(self):
        """Submitting with missing fields redirects with an error code."""
        response = self._confirm(
            {
                "name": "",
                "email": "test@example.com",
                "when": "2021-03-01T10:00:00+00:00",
            }
        )
        self.assertIn("error=missing_fields", response.url)

    def test_confirm_missing_when(self):
        """Submitting with missing datetime redirects with an error code."""
        response = self._confirm(
            {"name": "Test User", "email": "test@example.com", "when": ""}
        )
        self.assertIn("error=missing_fields", response.url)

    def test_confirm_invalid_date(self):
        """Submitting with invalid datetime redirects with an error code."""
        response = self._confirm(
            {"name": "Test User", "email": "test@example.com", "when": "not-a-date"}
        )
        self.assertIn("error=invalid_date", response.url)

    def test_confirm_invalid_email(self):
        """A malformed email is refused server-side."""
        response = self._confirm(
            {
                "name": "Test User",
                "email": "not-an-email",
                "when": "2021-03-01T10:00:00+00:00",
            }
        )
        self.assertIn("error=invalid_email", response.url)
        self.assertFalse(
            self.env["res.partner"].search([("email", "=", "not-an-email")])
        )

    def test_confirm_honeypot_rejected(self):
        """A filled honeypot field rejects the submission without side effects."""
        response = self._confirm(
            {
                "name": "Bot",
                "email": "bot@example.com",
                "when": "2021-03-01T10:00:00+00:00",
                "company_website": "http://spam.example.com",
            }
        )
        self.assertIn("error=rejected", response.url)
        self.assertFalse(self._booking_for("bot@example.com"))
        self.assertFalse(
            self.env["res.partner"].search([("email", "=", "bot@example.com")])
        )

    def test_confirm_rejects_off_grid_time(self):
        """Only the slots the page offers can be booked.

        10:07 is inside the working hours but not on the 30-minute grid.
        """
        response = self._confirm(
            {
                "name": "Off Grid",
                "email": "offgrid@example.com",
                "when": "2021-03-01T10:07:00+00:00",
            }
        )
        self.assertIn("error=slot_taken", response.url)
        self.assertIn("/book/test-booking/2021/3?", response.url)
        self.assertFalse(self._booking_for("offgrid@example.com"))

    def test_confirm_rejects_time_inside_deadline(self):
        """A slot inside the modification deadline is not bookable.

        Time is frozen on Friday 2021-02-26 09:00 UTC; there is no attendance
        on Fridays anyway, so use a Monday slot of the *previous* week which
        the calendar would otherwise accept as fitting the working hours.
        """
        response = self._confirm(
            {
                "name": "Too Late",
                "email": "late@example.com",
                "when": "2021-02-22T10:00:00+00:00",
            }
        )
        self.assertIn("error=slot_taken", response.url)
        self.assertFalse(self._booking_for("late@example.com"))

    def test_error_code_unknown_is_ignored(self):
        """Arbitrary text in ``?error=`` is never rendered."""
        page = self._url_xml("/book/test-booking?error=Call+this+number+now")
        self.assertFalse(page.cssselect(".o_wab_error"))
        page = self._url_xml("/book/test-booking?error=invalid_date")
        self.assertTrue(page.cssselect(".o_wab_error:contains('Invalid date')"))

    def test_success_page_renders(self):
        """Success page renders properly."""
        page = self._url_xml("/book/test-booking/success")
        self.assertTrue(page.cssselect("h1:contains('Booking Confirmed')"))

    def test_existing_partner_reused(self):
        """If partner with same email exists, it is reused and not renamed."""
        self.env["res.partner"].create(
            {"name": "Existing User", "email": "existing@example.com"}
        )
        self._confirm(
            {
                "name": "Somebody Else",
                "email": "existing@example.com",
                "when": "2021-03-01T10:00:00+00:00",
            }
        )
        partners = self.env["res.partner"].search(
            [("email", "=ilike", "existing@example.com")]
        )
        self.assertEqual(len(partners), 1)
        self.assertEqual(partners.name, "Existing User")

    def test_website_description_displayed(self):
        """Website description is shown on the booking page."""
        self.rbt.website_description = "<p>Welcome to our booking page!</p>"
        page = self._url_xml("/book/test-booking")
        self.assertTrue(page.cssselect(":contains('Welcome to our booking page!')"))

    def test_location_pill_displayed(self):
        """Location is shown as a pill on the booking page."""
        self.rbt.location = "Main office"
        page = self._url_xml("/book/test-booking")
        self.assertTrue(page.cssselect(".o_wab_meta_pill:contains('Main office')"))

    def test_sitemap_lists_published_page(self):
        """The public page is part of the website sitemap."""
        response = self.url_open("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/book/test-booking<", response.content)
        self.assertNotIn(b"/book/test-booking/success", response.content)

    def test_booking_page_default_tz_label(self):
        """Without a ``?tz=`` override the label reflects the resource tz."""
        page = self._url_xml("/book/test-booking/2021/3")
        labels = page.cssselect("#o_wab_tz_label")
        self.assertTrue(labels)
        resource_tz = self.rbt.resource_calendar_id.tz or "UTC"
        self.assertEqual(labels[0].text_content().strip(), resource_tz)
        calendar_root = page.cssselect(".o_wab_calendar")
        self.assertEqual(calendar_root[0].get("data-resource-tz"), resource_tz)
        self.assertEqual(calendar_root[0].get("data-effective-tz"), resource_tz)

    def test_booking_page_with_visitor_tz_override(self):
        """``?tz=Pacific/Auckland`` buckets slots into NZ-local dates."""

        def _slots(url):
            page = self._url_xml(url)
            slot_data_el = page.cssselect("#o_wab_slot_data")
            self.assertTrue(slot_data_el)
            return json.loads(slot_data_el[0].get("data-slots") or "[]")

        default_slots = _slots("/book/test-booking/2021/3")
        nz_slots = _slots("/book/test-booking/2021/3?tz=Pacific/Auckland")
        default_by_iso = {s["iso"]: s["date"] for s in default_slots}
        nz_by_iso = {s["iso"]: s["date"] for s in nz_slots}
        shared_isos = set(default_by_iso) & set(nz_by_iso)
        self.assertTrue(shared_isos)
        self.assertTrue(
            [iso for iso in shared_isos if default_by_iso[iso] != nz_by_iso[iso]],
            "bucketing did not move between resource tz and Pacific/Auckland",
        )
        page = self._url_xml("/book/test-booking/2021/3?tz=Pacific/Auckland")
        self.assertEqual(
            page.cssselect("#o_wab_tz_label")[0].text_content().strip(),
            "Pacific/Auckland",
        )
        calendar_root = page.cssselect(".o_wab_calendar")
        self.assertEqual(calendar_root[0].get("data-effective-tz"), "Pacific/Auckland")

    def test_booking_page_invalid_tz_falls_back(self):
        """A bogus ``?tz=`` value falls back to the resource tz."""
        page = self._url_xml("/book/test-booking/2021/3?tz=Etc/UTC%00malicious")
        calendar_root = page.cssselect(".o_wab_calendar")
        self.assertTrue(calendar_root)
        resource_tz = self.rbt.resource_calendar_id.tz or "UTC"
        self.assertEqual(calendar_root[0].get("data-effective-tz"), resource_tz)

    def test_booking_page_accepts_pytz_alias(self):
        """Deprecated IANA aliases the browser may emit are accepted."""
        page = self._url_xml("/book/test-booking/2021/3?tz=Asia/Calcutta")
        calendar_root = page.cssselect(".o_wab_calendar")
        self.assertEqual(calendar_root[0].get("data-effective-tz"), "Asia/Calcutta")

    def test_booking_page_has_display_tz_input(self):
        """The booking form ships a hidden ``display_tz`` input."""
        page = self._url_xml("/book/test-booking/2021/3")
        inputs = page.cssselect("#o_wab_display_tz")
        self.assertTrue(inputs)
        self.assertEqual(inputs[0].get("name"), "display_tz")

    def test_confirm_uses_display_tz_for_success_page(self):
        """``display_tz`` controls how the success-page time is rendered.

        10:00 UTC with ``display_tz=Pacific/Auckland`` (NZDT, UTC+13 in March
        2021) renders as 23:00 with a "Pacific/Auckland" label.
        """
        response = self._confirm(
            {
                "name": "NZ Visitor",
                "email": "nz@example.com",
                "when": "2021-03-01T10:00:00+00:00",
                "display_tz": "Pacific/Auckland",
            }
        )
        self.assertIn("/book/test-booking/success", response.url)
        booking = self._booking_for("nz@example.com")
        self.assertTrue(booking)
        self.assertEqual(booking.start.hour, 10)
        success_page = fromstring(response.content)
        rendered = " ".join(
            c.text_content() for c in success_page.cssselect(".o_wab_detail_value")
        )
        self.assertIn("23:00", rendered)
        self.assertIn("Pacific/Auckland", rendered)

    def test_confirm_rejects_malicious_offset(self):
        """A client lying about the iso offset cannot book outside the slots.

        ``2021-03-01T13:00:00+09:00`` is 04:00 UTC: inside no attendance, so
        the booking is refused, and nothing is created.
        """
        response = self._confirm(
            {
                "name": "Trickster",
                "email": "trick@example.com",
                "when": "2021-03-01T13:00:00+09:00",
                "display_tz": "America/New_York",
            }
        )
        self.assertIn("error=slot_taken", response.url)
        self.assertFalse(self._booking_for("trick@example.com"))

    def test_confirm_offset_normalised(self):
        """An offset iso that lands on a real slot books that UTC instant."""
        response = self._confirm(
            {
                "name": "Offset",
                "email": "offset@example.com",
                # 12:00+02:00 == 10:00 UTC, an offered slot
                "when": "2021-03-01T12:00:00+02:00",
            }
        )
        self.assertIn("/success", response.url)
        booking = self._booking_for("offset@example.com")
        self.assertEqual(booking.start, datetime(2021, 3, 1, 10, 0))


@freeze_time("2021-02-26 09:00:00", tick=True)
@tagged("post_install", "-at_install")
class TestBookingRaceCondition(HttpCase):
    """Race condition handling with a single resource combination.

    A separate class so the combination limiting and pre-booking happen in
    ``setUpClass``, making them visible to the HTTP server thread.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        cls.rbt.write({"is_published": True, "website_slug": "race-test"})
        # Limit to 1 combination so there is a real conflict
        cls.rbt.combination_rel_ids[1:].unlink()
        booking = cls.env["resource.booking"].create(
            {
                "type_id": cls.rbt.id,
                "partner_ids": [(4, cls.partner.id)],
                "combination_auto_assign": True,
            }
        )
        booking.start = datetime(2021, 3, 1, 10, 0)
        booking.action_confirm()

    def test_confirm_race_condition(self):
        """Double-booking the same slot shows an error message."""
        response = self.url_open("/book/race-test/2021/3")
        csrf = fromstring(response.content).cssselect('input[name="csrf_token"]')[0]
        data = {
            "csrf_token": csrf.get("value"),
            "name": "Late Visitor",
            "email": "late@example.com",
            "when": "2021-03-01T10:00:00+00:00",
        }
        response = self.url_open("/book/race-test/confirm", data=data, timeout=30)
        self.assertNotIn("/success", response.url)
        self.assertIn("error=slot_taken", response.url)
