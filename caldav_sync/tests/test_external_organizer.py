from odoo.tests import TransactionCase

from .common import CaldavTestCommon
from .test_calendar import _get_ics_path, _patch_caldav_with_events_from_ics


class TestExternalOrganizer(TransactionCase, CaldavTestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls._generate_user(
            "test",
            caldav_username="test",
            caldav_password="test",
            caldav_url="https://example.com/calendar",
        )

    def test_external_organizer_event_sync(self):
        """Test that events with external organizers are handled correctly."""
        # Setup mock for CalDAV client with our test ICS file
        with _patch_caldav_with_events_from_ics(
            [_get_ics_path("test_external_organizer.ics")], self.user
        ):
            # Ensure caldav is enabled
            self.user._compute_is_caldav_enabled()
            # Sync events from the mock server
            self.env["calendar.event"].poll_caldav_server()

            # Find the synced event
            event = self.env["calendar.event"].search(
                [("caldav_uid", "=", "external-organizer-test-123")]
            )

            # Verify event was created
            self.assertTrue(event, "Event should be created")

            # Verify user_id is False for external organizer
            self.assertFalse(
                event.user_id,
                "Event with external organizer should have user_id set to False",
            )

            # Verify the organizer's email is preserved in attendees
            external_attendee = event.attendee_ids.filtered(
                lambda a: a.email == "external.person@otherdomain.com"
            )
            self.assertTrue(
                external_attendee,
                "External organizer should be present in attendees",
            )
            # The external organizer should be in the attendees list
            self.assertTrue(
                external_attendee,
                "External organizer should be present in attendees list",
            )

    def test_no_organizer_external_event_sync(self):
        """Test that events without organizers are assigned to the calendar's user."""
        # Setup mock for CalDAV client with our test ICS file
        with _patch_caldav_with_events_from_ics(
            [_get_ics_path("test_external_no_organizer.ics")], self.user
        ):
            self.user._compute_is_caldav_enabled()
            # Make sure that the current user is not the admin user
            self.assertNotEqual(self.user.id, self.env.ref("base.user_admin").id)
            self.env["calendar.event"].poll_caldav_server()

            # Find the synced event
            event = self.env["calendar.event"].search(
                [("caldav_uid", "=", "external-organizer-test-123")]
            )

            # Verify event was created
            self.assertTrue(event, "Event should be created")

            # Verify user_id is set to the calendar's user
            self.assertEqual(
                event.user_id,
                self.user,
                "Event without organizer should have user_id set to calendar's user",
            )
