# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from freezegun import freeze_time
from lxml.html import fromstring

from odoo.tests.common import HttpCase

from .common import create_test_data


@freeze_time("2021-02-26 09:00:00", tick=True)
class PortalCase(HttpCase):
    def setUp(self):
        super().setUp()
        create_test_data(self)
        self.user_portal, self.user_manager = self.env["res.users"].create(
            [
                {
                    "name": "portal",
                    "login": "ptl",
                    "password": "ptl",
                    "groups_id": [(4, self.env.ref("base.group_portal").id, 0)],
                },
                {
                    "name": "manager",
                    "login": "mgr",
                    "password": "mgr",
                    "groups_id": [
                        (4, self.env.ref("resource_booking.group_manager").id, 0)
                    ],
                },
            ]
        )

    def _url_xml(self, url, data=None, timeout=10):
        """Open an URL and return the lxml etree object resulting from its content."""
        response = self.url_open(url, data, timeout=timeout)
        return fromstring(response.content)

    def test_portal_no_bookings(self):
        self.authenticate("ptl", "ptl")
        page = fromstring(self.url_open("/my").content)
        self.assertTrue(page.cssselect(".o_portal_docs"))
        self.assertFalse(page.cssselect('.o_portal_docs a:contains("Bookings")'))

    def test_portal_list_with_bookings(self):
        # Create one pending booking
        booking = self.env["resource.booking"].create(
            {"partner_id": self.user_portal.partner_id.id, "type_id": self.rbt.id}
        )
        self.authenticate("ptl", "ptl")
        # Main portal page contains bookings count
        page = self._url_xml("/my")
        link = page.cssselect('.o_portal_docs a:contains("Bookings")')[0]
        self.assertEqual(link.cssselect(".badge")[0].text.strip(), "1")
        # Bookings page lists 1 booking
        page = self._url_xml(link.get("href"))
        self.assertEqual(len(page.cssselect(".o_portal_my_doc_table tr")), 2)
        link = page.cssselect('.o_portal_my_doc_table a:contains("%d")' % booking.id)[0]
        # Booking page has schedule button
        page = self._url_xml(link.get("href"))
        self.assertTrue(page.cssselect('.badge:contains("Pending")'))

    def test_portal_scheduling_conflict(self):
        """Produce a scheduling conflict and see how UI behaves.

        This test would be better as a tour, but since there are a few back and
        forth actions among backend and frontend, and among distinct portal
        users, it seemed easier to do it completely on python.
        """
        # Set RBT to have only 1 combination available: the one for Mondays
        self.rbt.combination_rel_ids[1:].unlink()
        # One booking for portal user, another for a partner without user
        bookings = self.env["resource.booking"].create(
            [
                {
                    "partner_id": self.user_portal.partner_id.id,
                    "type_id": self.rbt.id,
                    "duration": 1,
                },
                {
                    "partner_id": self.partner.id,
                    "type_id": self.rbt.id,
                    "location": "Office 2",
                },
            ]
        )
        booking_public = bookings[1]
        # We assume they were invited by email and clicked on their links
        portal_url, public_url = (one.get_portal_url() for one in bookings)
        # Portal guy goes to scheduling page
        portal_page = self._url_xml(portal_url)
        self.assertTrue(portal_page.cssselect('.badge:contains("Pending")'))
        self.assertTrue(
            portal_page.cssselect(':contains("Duration:") + :contains("01:00")')
        )
        self.assertTrue(
            portal_page.cssselect(':contains("Location:") + :contains("Main office")')
        )
        link = portal_page.cssselect('a:contains("Schedule")')[0]
        portal_url = link.get("href")
        portal_page = self._url_xml(portal_url)
        # Nothing free on February, he goes to March
        self.assertTrue(
            portal_page.cssselect(".o_booking_calendar:contains('February 2021')")
        )
        self.assertTrue(
            portal_page.cssselect(
                ".o_booking_calendar td"
                ":contains('All times are displayed using this timezone:')"
                ":contains('UTC')"
            )
        )
        self.assertFalse(portal_page.cssselect(".o_booking_calendar .dropdown"))
        self.assertFalse(portal_page.cssselect(".o_booking_calendar form"))
        link = portal_page.cssselect('a[title="Next month"]')[0]
        portal_url = link.get("href")
        portal_page = self._url_xml(portal_url)
        self.assertTrue(
            portal_page.cssselect(".o_booking_calendar:contains('March 2021')")
        )
        self.assertTrue(portal_page.cssselect(".o_booking_calendar .dropdown"))
        self.assertTrue(portal_page.cssselect(".o_booking_calendar form"))
        # Public guy does the same
        public_page = self._url_xml(public_url)
        self.assertTrue(
            public_page.cssselect(':contains("Duration:") + :contains("00:30")')
        )
        self.assertTrue(
            public_page.cssselect(':contains("Location:") + :contains("Office 2")')
        )
        self.assertTrue(public_page.cssselect('.badge:contains("Pending")'))
        link = public_page.cssselect('a:contains("Schedule")')[0]
        public_url = link.get("href")
        public_page = self._url_xml(public_url)
        self.assertTrue(
            public_page.cssselect(".o_booking_calendar:contains('February 2021')")
        )
        self.assertTrue(
            public_page.cssselect(
                ".o_booking_calendar td"
                ":contains('All times are displayed using this timezone:')"
                ":contains('UTC')"
            )
        )
        self.assertFalse(public_page.cssselect(".o_booking_calendar .dropdown"))
        self.assertFalse(public_page.cssselect(".o_booking_calendar form"))
        link = public_page.cssselect('a[title="Next month"]')[0]
        public_url = link.get("href")
        public_page = self._url_xml(public_url)
        self.assertTrue(
            public_page.cssselect(".o_booking_calendar:contains('March 2021')")
        )
        self.assertTrue(public_page.cssselect(".o_booking_calendar .dropdown"))
        self.assertTrue(public_page.cssselect(".o_booking_calendar form"))
        # Public guy makes reservation next Monday at 10:00
        slot = datetime(2021, 3, 1, 10).timestamp()
        selector_10am = (
            "#dropdown-trigger-2021-03-01 "
            "+ .slots-dropdown .dropdown-item:contains('10:00')"
        )
        selector_1030am = (
            "#dropdown-trigger-2021-03-01 "
            "+ .slots-dropdown .dropdown-item:contains('10:30')"
        )
        self.assertTrue(public_page.cssselect(selector_10am))
        self.assertTrue(public_page.cssselect(selector_1030am))
        form = public_page.cssselect("form#modal-confirm-%d" % slot)[0]
        public_url = form.get("action")
        data = {
            element.get("name"): element.get("value")
            for element in form.cssselect("input")
        }
        public_page = self._url_xml(public_url, data)
        # Public guy's reservation succeeded
        self.assertTrue(public_page.cssselect('.badge:contains("Confirmed")'))
        self.assertTrue(
            public_page.cssselect(
                'div:contains("Booked resources:")'
                ':contains("Material resource for Mon")'
                ':contains("User User 0")'
            )
        )
        self.assertTrue(
            public_page.cssselect('div:contains("Location:"):contains("Office 2")')
        )
        self.assertTrue(
            public_page.cssselect(
                'div:contains("Dates:")'
                ':contains("03/01/2021 at (10:00:00 To 10:30:00) (UTC)")'
            )
        )
        # Public guy's booking and related meeting are OK in backend
        booking_public.invalidate_cache(ids=booking_public.ids)
        self.assertEqual(booking_public.state, "confirmed")
        self.assertEqual(len(booking_public.meeting_id.attendee_ids), 2)
        for attendee in booking_public.meeting_id.attendee_ids:
            self.assertTrue(attendee.partner_id)
            self.assertIn(
                attendee.partner_id,
                self.partner | self.users[0].partner_id,
            )
            self.assertEqual(
                attendee.state,
                "accepted" if attendee.partner_id == self.partner else "needsAction",
            )
        # At the same time, portal guy tries to reserve the same slot, which
        # appears as free to him due to the race condition we just created
        self.assertTrue(portal_page.cssselect(selector_10am))
        self.assertTrue(portal_page.cssselect(selector_1030am))
        form = portal_page.cssselect("form#modal-confirm-%d" % slot)[0]
        portal_url = form.get("action")
        data = {
            element.get("name"): element.get("value")
            for element in form.cssselect("input")
        }
        portal_page = self._url_xml(portal_url, data)
        # He's back on the March calendar view, with an error message
        self.assertTrue(
            portal_page.cssselect(
                ".alert-danger:contains('The chosen schedule is no longer available.')"
            )
        )
        self.assertTrue(
            portal_page.cssselect(".o_booking_calendar:contains('March 2021')")
        )
        self.assertTrue(portal_page.cssselect(".o_booking_calendar .dropdown"))
        self.assertTrue(portal_page.cssselect(".o_booking_calendar form"))
        # He can't select that slot anymore, so he books it 30 minutes later
        self.assertFalse(portal_page.cssselect(selector_10am))
        self.assertTrue(portal_page.cssselect(selector_1030am))
        slot = datetime(2021, 3, 1, 10, 30).timestamp()
        self.assertTrue(portal_page.cssselect("#dropdown-trigger-2021-03-08"))
        form = portal_page.cssselect("form#modal-confirm-%d" % slot)[0]
        portal_url = form.get("action")
        data = {
            element.get("name"): element.get("value")
            for element in form.cssselect("input")
        }
        portal_page = self._url_xml(portal_url, data)
        # Portal guy's reservation succeeded
        self.assertTrue(portal_page.cssselect('.badge:contains("Confirmed")'))
        self.assertTrue(
            portal_page.cssselect(
                'div:contains("Booked resources:")'
                ':contains("Material resource for Mon")'
                ':contains("User User 0")'
            )
        )
        self.assertTrue(
            portal_page.cssselect('div:contains("Location:"):contains("Main office")')
        )
        self.assertTrue(
            portal_page.cssselect(
                'div:contains("Dates:")'
                ':contains("03/01/2021 at (10:30:00 To 11:30:00) (UTC)")'
            )
        )
        # Portal guy cancels
        link = portal_page.cssselect('a:contains("Cancel this booking")')[0]
        portal_url = link.get("href")
        portal_page = self._url_xml(portal_url)
        self.assertTrue(portal_page.cssselect(".oe_login_form"))
