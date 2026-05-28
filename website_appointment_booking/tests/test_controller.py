# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from datetime import datetime

from freezegun import freeze_time
from lxml.html import fromstring

from odoo.tests import tagged
from odoo.tests.common import HttpCase

from odoo.addons.resource_booking.tests.common import create_test_data


@freeze_time("2021-02-26 09:00:00", tick=True)
@tagged("post_install", "-at_install")
class TestWebsiteAppointmentBooking(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        cls.rbt.write(
            {
                "website_published": True,
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
        # The page should show the booking type name
        self.assertTrue(
            page.cssselect(".o_wab_title:contains('Test resource booking type')")
        )
        # Duration pill should be present
        self.assertTrue(page.cssselect(".o_wab_meta_pill:contains('30 min')"))

    def test_booking_page_february_no_slots(self):
        """February 2021 has no available Monday/Tuesday slots (too close)."""
        page = self._url_xml("/book/test-booking")
        # February should have no available slots (within modification deadline)
        self.assertTrue(
            page.cssselect(".o_wab_empty_month:contains('No available slots')")
        )

    def test_booking_page_march_has_slots(self):
        """March 2021 should have available slots on Mondays and Tuesdays."""
        page = self._url_xml("/book/test-booking/2021/3")
        self.assertTrue(page.cssselect(".o_wab_month_label:contains('March 2021')"))
        # Should have slot data in hidden JSON element
        slot_data_el = page.cssselect("#o_wab_slot_data")
        self.assertTrue(slot_data_el)
        # Calendar table should be present
        self.assertTrue(page.cssselect(".o_wab_table"))

    def test_booking_page_navigation(self):
        """Month navigation links work."""
        page = self._url_xml("/book/test-booking/2021/3")
        # Should have a next month link
        next_links = page.cssselect('a[href*="/book/test-booking/2021/4"]')
        self.assertTrue(next_links)

    def test_confirm_creates_booking(self):
        """Successful form submission creates a confirmed booking."""
        # First load the booking page to get a session and CSRF token
        page = self._url_xml("/book/test-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "Test Visitor",
            "email": "visitor@example.com",
            "when": "2021-03-01T10:00:00+00:00",
        }
        response = self.url_open("/book/test-booking/confirm", data=data, timeout=30)
        # Should redirect to success page
        self.assertIn("/book/test-booking/success", response.url)
        # Verify booking was created in backend
        booking = self.env["resource.booking"].search(
            [
                ("type_id", "=", self.rbt.id),
                ("partner_ids.email", "=", "visitor@example.com"),
            ]
        )
        self.assertTrue(booking)
        self.assertEqual(booking.state, "confirmed")
        self.assertTrue(booking.meeting_id)
        # Verify partner was created
        partner = self.env["res.partner"].search(
            [("email", "=ilike", "visitor@example.com")]
        )
        self.assertTrue(partner)
        self.assertEqual(partner.name, "Test Visitor")

    def test_confirm_missing_fields(self):
        """Submitting with missing fields redirects with error."""
        page = self._url_xml("/book/test-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "",
            "email": "test@example.com",
            "when": "2021-03-01T10:00:00+00:00",
        }
        response = self.url_open("/book/test-booking/confirm", data=data)
        self.assertIn("error=", response.url)

    def test_confirm_missing_when(self):
        """Submitting with missing datetime redirects with error."""
        page = self._url_xml("/book/test-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "Test User",
            "email": "test@example.com",
            "when": "",
        }
        response = self.url_open("/book/test-booking/confirm", data=data)
        self.assertIn("error=", response.url)

    def test_confirm_invalid_date(self):
        """Submitting with invalid datetime redirects with error."""
        page = self._url_xml("/book/test-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "Test User",
            "email": "test@example.com",
            "when": "not-a-date",
        }
        response = self.url_open("/book/test-booking/confirm", data=data)
        self.assertIn("error=", response.url)

    def test_success_page_renders(self):
        """Success page renders properly."""
        page = self._url_xml("/book/test-booking/success")
        self.assertTrue(page.cssselect("h1:contains('Booking Confirmed')"))

    def test_existing_partner_reused(self):
        """If partner with same email exists, it is reused."""
        self.env["res.partner"].create(
            {"name": "Existing User", "email": "existing@example.com"}
        )
        page = self._url_xml("/book/test-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "Existing User",
            "email": "existing@example.com",
            "when": "2021-03-01T10:00:00+00:00",
        }
        self.url_open("/book/test-booking/confirm", data=data, timeout=30)
        partners = self.env["res.partner"].search(
            [("email", "=ilike", "existing@example.com")]
        )
        self.assertEqual(len(partners), 1)

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
        """``?tz=Pacific/Auckland`` buckets slots into NZ-local dates.

        Compares against the default-tz (no ``?tz=``) response and asserts
        that at least one shared slot iso ends up under a different date
        key — i.e. bucketing actually moved between timezones.
        """

        def _slots(url):
            page = self._url_xml(url)
            slot_data_el = page.cssselect("#o_wab_slot_data")
            self.assertTrue(slot_data_el)
            return json.loads(slot_data_el[0].get("data-slots") or "[]")

        default_slots = _slots("/book/test-booking/2021/3")
        nz_slots = _slots("/book/test-booking/2021/3?tz=Pacific/Auckland")

        # Same set of iso instants on both, just different ``date`` buckets.
        default_by_iso = {s["iso"]: s["date"] for s in default_slots}
        nz_by_iso = {s["iso"]: s["date"] for s in nz_slots}
        shared_isos = set(default_by_iso) & set(nz_by_iso)
        self.assertTrue(
            shared_isos, "expected at least one slot shared across timezones"
        )
        differing = [
            iso for iso in shared_isos if default_by_iso[iso] != nz_by_iso[iso]
        ]
        self.assertTrue(
            differing,
            "expected at least one slot's date key to differ between resource tz "
            "and Pacific/Auckland — bucketing didn't move",
        )

        page = self._url_xml("/book/test-booking/2021/3?tz=Pacific/Auckland")
        labels = page.cssselect("#o_wab_tz_label")
        self.assertTrue(labels)
        self.assertEqual(labels[0].text_content().strip(), "Pacific/Auckland")
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
        """Deprecated IANA aliases the browser may emit are accepted.

        ``Asia/Calcutta`` is a pytz-resolvable alias for ``Asia/Kolkata``;
        modern browsers may still report it on some platforms. Membership
        against ``pytz.all_timezones_set`` would reject it — ``pytz.timezone``
        accepts it. Make sure the validator does too.
        """
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

        Submit a 10:00 UTC Monday slot with ``display_tz=Pacific/Auckland``
        — NZ was NZDT (UTC+13) in March 2021, so the rendered time on the
        success page must be 23:00 with a "Pacific/Auckland" label, not
        the resource-tz formatting of the same instant.
        """
        page = self._url_xml("/book/test-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "NZ Visitor",
            "email": "nz@example.com",
            "when": "2021-03-01T10:00:00+00:00",
            "display_tz": "Pacific/Auckland",
        }
        response = self.url_open("/book/test-booking/confirm", data=data, timeout=30)
        self.assertIn("/book/test-booking/success", response.url)

        # Backend booking still stores the canonical UTC instant.
        booking = self.env["resource.booking"].search(
            [("partner_ids.email", "=", "nz@example.com")], limit=1
        )
        self.assertTrue(booking)
        self.assertEqual(booking.start.replace(tzinfo=None).hour, 10)

        # Success page renders in the visitor's tz, not the resource tz.
        success_page = fromstring(response.content)
        time_cells = success_page.cssselect(".o_wab_detail_value")
        rendered = " ".join(c.text_content() for c in time_cells)
        self.assertIn("23:00", rendered)
        self.assertIn("Pacific/Auckland", rendered)

    def test_confirm_rejects_malicious_offset(self):
        """A client lying about the iso offset can't fake the success page.

        Submit ``when=2021-03-01T13:00:00+09:00`` — that's 04:00 UTC, not
        13:00. With ``display_tz=America/New_York`` (EST = UTC-5 in March
        before DST), the canonical rendering is 23:00 on Feb 28 — *not*
        the 13:00 the client tried to assert via the offset.

        Choose the +09:00 hours so the laundered UTC instant lands inside
        the test calendar's available slots (Mondays 8-12 Madrid), keeping
        the test deterministic about whether the booking is created.
        """
        page = self._url_xml("/book/test-booking/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "Trickster",
            "email": "trick@example.com",
            # 13:00+09:00 = 04:00 UTC = 05:00 CET (Madrid) → in-window
            "when": "2021-03-01T13:00:00+09:00",
            "display_tz": "America/New_York",
        }
        response = self.url_open("/book/test-booking/confirm", data=data, timeout=30)
        # Booking storage time is the canonical UTC instant.
        booking = self.env["resource.booking"].search(
            [("partner_ids.email", "=", "trick@example.com")], limit=1
        )
        if booking:
            self.assertEqual(booking.start.replace(tzinfo=None).hour, 4)
        # The success page (if reached) must show the ET rendering of
        # the canonical 04:00 UTC instant (= 23:00 EST on Feb 28), NOT
        # the 13:00 the client embedded in the iso.
        if "/success" in response.url:
            success_page = fromstring(response.content)
            time_cells = success_page.cssselect(".o_wab_detail_value")
            rendered = " ".join(c.text_content() for c in time_cells)
            self.assertNotIn("13:00", rendered)
            self.assertIn("23:00", rendered)
            self.assertIn("America/New_York", rendered)

    # ---- Out-of-hours request flow ----

    def test_request_banner_hidden_for_resource_tz_visitor(self):
        """Domestic visitor (same tz as resource) never sees the banner."""
        page = self._url_xml("/book/test-booking/2021/3")
        banners = page.cssselect(".o_wab_request_banner")
        self.assertFalse(
            banners,
            "request banner should not render when effective_tz == resource_tz",
        )

    def test_request_banner_shown_for_far_tz_with_no_overlap(self):
        """Pacific/Auckland visitor sees the banner when the resource
        calendar's published hours don't overlap with 9–17 NZ-local.

        The OCA test fixture's calendar is Europe/Madrid Mon/Tue 8–12 +
        16–20 — none of those map to 9–17 NZST (~UTC+13), so the banner
        should show.
        """
        page = self._url_xml("/book/test-booking/2021/3?tz=Pacific/Auckland")
        banners = page.cssselect(".o_wab_request_banner")
        self.assertTrue(
            banners,
            "request banner should render when visitor has no working-hours overlap",
        )
        # Form is present, hidden until toggle click
        forms = page.cssselect("form.o_wab_request_form")
        self.assertTrue(forms)
        self.assertIn("d-none", forms[0].get("class") or "")
        # Hidden visitor_tz input pre-populated
        tz_inputs = page.cssselect('input[name="visitor_tz"]')
        self.assertTrue(tz_inputs)
        self.assertEqual(tz_inputs[0].get("value"), "Pacific/Auckland")

    def test_booking_request_creates_tagged_lead(self):
        """POST /book/<slug>/request creates a CRM lead with the right tag."""
        page = self._url_xml("/book/test-booking?tz=Pacific/Auckland")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "NZ Requester",
            "email": "request-test@example.com",
            "preferred_window": "Tue/Thu 09:00-11:00 NZST",
            "note": "Need to chat about ERP migration",
            "visitor_tz": "Pacific/Auckland",
        }
        response = self.url_open("/book/test-booking/request", data=data, timeout=30)
        # Redirects back to booking page with the success flag
        self.assertIn("request_success=1", response.url)

        # Lead created with the tag attached
        lead = self.env["crm.lead"].search(
            [("email_from", "=", "request-test@example.com")], limit=1
        )
        self.assertTrue(lead)
        tag_names = lead.tag_ids.mapped("name")
        self.assertIn("intl-after-hours-request", tag_names)
        # Tz + preferred window are in the description for operator review
        self.assertIn("Pacific/Auckland", lead.description)
        self.assertIn("Tue/Thu 09:00-11:00 NZST", lead.description)

    def test_booking_request_missing_name_redirects_with_error(self):
        """Submitting without name/email redirects with an error param."""
        page = self._url_xml("/book/test-booking?tz=Pacific/Auckland")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "",
            "email": "incomplete@example.com",
            "visitor_tz": "Pacific/Auckland",
        }
        response = self.url_open("/book/test-booking/request", data=data, timeout=10)
        self.assertIn("error=", response.url)

    def test_booking_request_success_banner_renders(self):
        """After ?request_success=1, the success banner appears."""
        page = self._url_xml("/book/test-booking?request_success=1")
        success = page.cssselect(".o_wab_success_banner")
        self.assertTrue(success, "success banner should render when ?request_success=1")


@freeze_time("2021-02-26 09:00:00", tick=True)
@tagged("post_install", "-at_install")
class TestBookingRaceCondition(HttpCase):
    """Test race condition handling with a single resource combination.

    Uses a separate class so that the combination limiting and pre-booking
    happen in ``setUpClass``, making them visible to the HTTP server thread.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        cls.rbt.write(
            {
                "website_published": True,
                "website_slug": "race-test",
            }
        )
        # Limit to 1 combination so there is a real conflict
        cls.rbt.combination_rel_ids[1:].unlink()
        # Book the only slot via backend
        when_naive = datetime(2021, 3, 1, 10, 0)
        booking = cls.env["resource.booking"].create(
            {
                "type_id": cls.rbt.id,
                "partner_ids": [(4, cls.partner.id)],
                "combination_auto_assign": True,
            }
        )
        booking.start = when_naive
        booking.action_confirm()

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

    def test_confirm_race_condition(self):
        """Double-booking the same slot shows an error message."""
        page = self._url_xml("/book/race-test/2021/3")
        csrf = self._get_csrf_token(page)
        data = {
            "csrf_token": csrf,
            "name": "Late Visitor",
            "email": "late@example.com",
            "when": "2021-03-01T10:00:00+00:00",
        }
        response = self.url_open("/book/race-test/confirm", data=data, timeout=30)
        # Should redirect back to calendar with error, not to success
        self.assertNotIn("/success", response.url)
        self.assertIn("error=", response.url)
