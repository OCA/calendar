from collections.abc import Iterable
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import caldav
import icalendar
from freezegun import freeze_time

from odoo.tests import TransactionCase, tagged

from .common import CaldavTestCommon

WEEKDAY_MAP = {
    0: "SUN",
    1: "MON",
    2: "TUE",
    3: "WED",
    4: "THU",
    5: "FRI",
    6: "SAT",
}


def _get_ics_path(filename):
    return Path(__file__).parent / "samples" / filename


def _load_ical_events(ics_paths):
    """Load and parse ICS files into icalendar.Calendar objects."""
    if not ics_paths:
        return []
    if not isinstance(ics_paths, Iterable):
        ics_paths = [ics_paths]
    events = []
    for ics_path in ics_paths:
        with ics_path.open("rb") as file:
            events.append(icalendar.Calendar.from_ical(file.read()))
    return events


def _update_event_timestamps(ical_events, last_modified):
    """Update last-modified and dtstamp on all VEVENT subcomponents."""
    for event in ical_events:
        for subcomponent in event.subcomponents:
            if subcomponent.name == "VEVENT":
                subcomponent["last-modified"] = icalendar.vDatetime(last_modified)
                subcomponent["dtstamp"] = icalendar.vDatetime(last_modified)


def _futurize_events(ical_events):
    """Shift event start/end times to now, preserving duration."""
    for event in ical_events:
        for subcomponent in event.subcomponents:
            if subcomponent.name == "VEVENT":
                start = subcomponent.get("dtstart") and subcomponent.decoded("dtstart")
                end = subcomponent.get("dtend") and subcomponent.decoded("dtend")
                duration = end - start
                subcomponent["dtstart"] = icalendar.vDDDTypes(datetime.now())
                subcomponent["dtend"] = icalendar.vDDDTypes(datetime.now() + duration)


def _build_caldav_events(ical_calendars):
    """Convert icalendar.Calendar objects to caldav.Event objects.

    Args:
        ical_calendars: List of icalendar.Calendar objects loaded from ICS files.

    Returns:
        List of caldav.Event objects. Each calendar is converted to a caldav.Event,
        preserving all VEVENT components (including those with recurrence-id).
    """
    # Each calendar from an ICS file becomes one caldav.Event
    # The calendar already contains all VEVENTs (base + exceptions)
    return [caldav.Event(data=cal.to_ical()) for cal in ical_calendars]


@contextmanager
def _patch_caldav_with_events_from_ics(
    ics_paths, user, last_modified=None, futurize=True
):
    """Context manager to patch caldav.DAVClient with events from ICS files."""
    with patch("caldav.DAVClient") as MockDAVClient:
        mock_client = MockDAVClient.return_value
        mock_calendars = {}

        def calendar_side_effect(url):
            if url not in mock_calendars:
                mock_cal = MagicMock()
                mock_cal.events = MagicMock(return_value=[])
                mock_cal.event_by_uid = MagicMock()
                mock_calendars[url] = mock_cal
            return mock_calendars[url]

        mock_client.calendar = calendar_side_effect
        mock_calendar = calendar_side_effect(user.caldav_calendar_url)

        ical_events = _load_ical_events(ics_paths)
        if last_modified:
            _update_event_timestamps(ical_events, last_modified)
        if futurize:
            _futurize_events(ical_events)

        caldav_events = _build_caldav_events(ical_events)
        mock_calendar.events.return_value = caldav_events
        user._compute_is_caldav_enabled()
        yield


@tagged("post_install", "-at_install")
class TestCalendarEvent(TransactionCase, CaldavTestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.users"].search([])._compute_is_caldav_enabled()
        cls.user_1_url = "https://mycaldav.test.com/test1calendar"
        cls.user_1 = cls._generate_user(
            "test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url=cls.user_1_url,
        )
        cls.user_2_url = "https://mycaldav.test.com/test2calendar"
        cls.user_2 = cls._generate_user(
            "test2",
            caldav_username="user2",
            caldav_password="pass2",
            caldav_url=cls.user_2_url,
        )
        cls.user_3_url = "https://mycaldav.test.com/test3calendar"
        cls.user_3 = cls._generate_user(
            "test3",
            caldav_username="user3",
            caldav_password="pass3",
            caldav_url=cls.user_3_url,
        )

    def test_basic_past_event_from_server_no_create(self):
        user = self.user_1
        ics_path = _get_ics_path("basic.ics")
        with _patch_caldav_with_events_from_ics(ics_path, user, futurize=False):
            current_events = self.env["calendar.event"].search([])
            self.env["calendar.event"].poll_caldav_server()
            events_after_sync = self.env["calendar.event"].search([])
            new_events = events_after_sync - current_events
            self.assertEqual(len(new_events), 0)

    def test_recurring_from_server_create(self):
        user = self.user_1
        ics_path = _get_ics_path("test_recurring.ics")
        with _patch_caldav_with_events_from_ics(ics_path, user):
            self.env["calendar.event"].poll_caldav_server()
        events = self.env["calendar.event"].search(
            [("partner_id", "=", user.partner_id.id)]
        )
        self.assertEqual(len(events), 10)

    @freeze_time("2024-10-07")
    def test_recurring_allday_from_server_create(self):
        """Test that all-day recurring events (with DATE instead of DATETIME) are
        handled.

        This tests the fix for the bug where dtstart.astimezone(utc) was called
        without checking if dtstart is a datetime (has astimezone) or a date (doesn't).
        """
        user = self.user_1
        ics_path = _get_ics_path("test_recurring_allday.ics")
        with _patch_caldav_with_events_from_ics(ics_path, user, futurize=False):
            self.env["calendar.event"].poll_caldav_server()
        events = self.env["calendar.event"].search(
            [("partner_id", "=", user.partner_id.id)]
        )
        self.assertEqual(len(events), 5)

    def test_multiple_attendees_event_from_server_create(self):
        user = self.user_1
        ics_path = _get_ics_path("test_multi_attendee.ics")
        with _patch_caldav_with_events_from_ics(ics_path, user):
            self.env["calendar.event"].poll_caldav_server()
        event = self.env["calendar.event"].search([("user_id", "=", user.id)])
        self.assertEqual(len(event.attendee_ids), 3)
        self.assertIn(user.partner_id, event.attendee_ids.partner_id)

    def test_multiple_attendees_event_from_server_update(self):
        user = self.user_1
        ics_path = _get_ics_path("test_multi_attendee.ics")
        with _patch_caldav_with_events_from_ics(ics_path, user):
            self.env["calendar.event"].poll_caldav_server()
        event = self.env["calendar.event"].search([("user_id", "=", user.id)])
        ics_path = _get_ics_path("test_multi_attendee_update.ics")
        # Use a future timestamp to ensure the update is not considered outdated
        future_time = datetime.now(timezone.utc) + timedelta(seconds=5)
        with _patch_caldav_with_events_from_ics(
            ics_path, user, last_modified=future_time
        ):
            self.env["calendar.event"].poll_caldav_server()
        # Refresh the event record after the update
        event.invalidate_recordset()
        self.assertEqual(len(event.attendee_ids), 2)
        self.assertIn(user.partner_id, event.attendee_ids.partner_id)

    def test_multiple_attendees_event_from_server_delete(self):
        user = self.user_1
        ics_path = _get_ics_path("test_multi_attendee.ics")
        with _patch_caldav_with_events_from_ics(ics_path, user):
            self.env["calendar.event"].poll_caldav_server()
        # Passing None as ics_path means no events returned from server
        with _patch_caldav_with_events_from_ics(None, user):
            self.env["calendar.event"].poll_caldav_server()
        event = self.env["calendar.event"].search([("user_id", "=", user.id)])
        self.assertFalse(event)

    def test_multiple_user_attendees_event_from_server_create(self):
        """Test event has:
        Organizer: user1 (test1@example.com)
        Attendees: user2 and user3 (test2@example.com, test3@example.com)
        """
        user1 = self.user_1
        user2 = self.user_2
        user3 = self.user_3
        ics_path = _get_ics_path("test_multi_user.ics")
        with _patch_caldav_with_events_from_ics(ics_path, user1):
            self.env["calendar.event"].poll_caldav_server()
        with _patch_caldav_with_events_from_ics(ics_path, user2):
            self.env["calendar.event"].poll_caldav_server()
        with _patch_caldav_with_events_from_ics(ics_path, user3):
            self.env["calendar.event"].poll_caldav_server()
        event = self.env["calendar.event"].search(
            [("caldav_uid", "=", "2495546B-5C9A-4632-AAD3-A179EF83CF20")]
        )
        self.assertEqual(len(event), 1)
        # Make sure the event wasn't duplicated all over the place
        other_user_events = self.env["calendar.event"].search(
            [("user_id", "in", [user2.id, user3.id])]
        )
        self.assertFalse(other_user_events)
        self.assertIn(user2.partner_id, event.partner_ids)
        self.assertIn(user3.partner_id, event.partner_ids)

    def test_multiple_user_attendees_event_from_server_update(self):
        """Test event has (as in above test):
        Organizer: user1 (test1@example.com)
        Attendees: user2 and user3 (test2@example.com, test3@example.com)
        """
        user1 = self.user_1
        user2 = self.user_2
        user3 = self.user_3
        ics_path = _get_ics_path("test_multi_user.ics")
        with _patch_caldav_with_events_from_ics(ics_path, user1):
            self.env["calendar.event"].poll_caldav_server()
        with _patch_caldav_with_events_from_ics(ics_path, user2):
            self.env["calendar.event"].poll_caldav_server()
        with _patch_caldav_with_events_from_ics(ics_path, user3):
            self.env["calendar.event"].poll_caldav_server()
        notification_method = (
            "odoo.addons.calendar.models.calendar_attendee"
            ".CalendarAttendee._notify_attendees"
        )
        # Now update it to remove one attendee
        # Shuffle the user polling order just to test more robustly
        ics_path = _get_ics_path("test_multi_user_update.ics")
        with (
            _patch_caldav_with_events_from_ics(
                ics_path, user2, last_modified=datetime.now(timezone.utc)
            ),
            patch(notification_method) as mock_notification_method,
        ):
            self.env["calendar.event"].poll_caldav_server()
            mock_notification_method.assert_not_called()
        with (
            _patch_caldav_with_events_from_ics(
                ics_path, user3, last_modified=datetime.now(timezone.utc)
            ),
            patch(notification_method) as mock_notification_method,
        ):
            self.env["calendar.event"].poll_caldav_server()
            mock_notification_method.assert_not_called()
        with (
            _patch_caldav_with_events_from_ics(
                ics_path, user1, last_modified=datetime.now(timezone.utc)
            ),
            patch(notification_method) as mock_notification_method,
        ):
            self.env["calendar.event"].poll_caldav_server()
            mock_notification_method.assert_not_called()
        event = self.env["calendar.event"].search(
            [("caldav_uid", "=", "2495546B-5C9A-4632-AAD3-A179EF83CF20")]
        )
        self.assertIn(user3.partner_id, event.partner_ids)
        self.assertNotIn(user2.partner_id, event.partner_ids)
        self.assertEqual(len(event.attendee_ids), 2)
