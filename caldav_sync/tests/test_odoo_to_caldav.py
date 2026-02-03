from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from odoo import Command
from odoo.tests import TransactionCase, tagged

from .common import CaldavTestCommon


@tagged("post_install", "-at_install")
class TestOdooToCalDAV(TransactionCase, CaldavTestCommon):
    """Tests for synchronizing Odoo calendar events to CalDAV server."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.users"].search([])._compute_is_caldav_enabled()
        cls.user_1_url = "https://mycaldav.test.com/test1calendar"
        cls.user_1 = cls._generate_user(
            "sync_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url=cls.user_1_url,
        )
        cls.user_2_url = "https://mycaldav.test.com/test2calendar"
        cls.user_2 = cls._generate_user(
            "sync_test2",
            caldav_username="user2",
            caldav_password="pass2",
            caldav_url=cls.user_2_url,
        )

    def _create_mock_caldav_client(self):
        """Create a mock CalDAV client with calendar."""
        mock_client = MagicMock()
        mock_calendar = MagicMock()
        mock_client.calendar.return_value = mock_calendar
        mock_calendar.events.return_value = []
        return mock_client, mock_calendar

    def test_non_caldav_user_event_does_not_sync(self):
        """Test that events for non-CalDAV users don't attempt to sync."""
        non_caldav_user = self._generate_user("non_caldav_user")

        with patch("caldav.DAVClient") as MockDAVClient:
            event = (
                self.env["calendar.event"]
                .with_user(non_caldav_user)
                .create(
                    {
                        "name": "Non-Sync Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([non_caldav_user.partner_id.id])],
                    }
                )
            )

        # DAVClient should not have been instantiated
        MockDAVClient.assert_not_called()
        self.assertTrue(event.exists())

    def test_caldav_no_sync_context_prevents_sync(self):
        """Test that caldav_no_sync context prevents syncing."""
        mock_client, mock_calendar = self._create_mock_caldav_client()

        with patch("caldav.DAVClient", return_value=mock_client):
            self.user_1._compute_is_caldav_enabled()
            self.env["calendar.event"].with_user(self.user_1).with_context(
                caldav_no_sync=True
            ).create(
                {
                    "name": "No Sync Event",
                    "start": datetime.now() + timedelta(days=1),
                    "stop": datetime.now() + timedelta(days=1, hours=1),
                    "partner_ids": [Command.set([self.user_1.partner_id.id])],
                }
            )

        mock_calendar.save_event.assert_not_called()


@tagged("post_install", "-at_install")
class TestEventDataCreation(TransactionCase, CaldavTestCommon):
    """Tests for event data creation methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.users"].search([])._compute_is_caldav_enabled()
        cls.user_1_url = "https://mycaldav.test.com/test1calendar"
        cls.user_1 = cls._generate_user(
            "data_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url=cls.user_1_url,
        )

    def test_create_event_data_basic(self):
        """Test _create_event_data returns correct structure."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Test Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        event_data = event._create_event_data()
        self.assertIn("uid", event_data)
        self.assertIn("summary", event_data)
        self.assertIn("dtstart", event_data)
        self.assertIn("dtend", event_data)
        self.assertIn("organizer", event_data)
        self.assertIn("attendee", event_data)
        self.assertEqual(str(event_data["summary"]), "Test Event")

    def test_create_event_data_with_description(self):
        """Test _create_event_data includes description."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Event With Desc",
                        "description": "<p>Test description</p>",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        event_data = event._create_event_data()
        self.assertIn("description", event_data)

    def test_create_event_data_with_location(self):
        """Test _create_event_data includes location."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Event With Location",
                        "location": "Room 101",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        event_data = event._create_event_data()
        self.assertIn("location", event_data)
        self.assertEqual(str(event_data["location"]), "Room 101")

    def test_html_to_text_conversion(self):
        """Test _html_to_text converts HTML to markdown."""
        CalendarEvent = self.env["calendar.event"]
        html = "<p>This is <strong>bold</strong> text</p>"
        result = CalendarEvent._html_to_text(html)
        self.assertIn("bold", result)
        self.assertNotIn("<strong>", result)

    def test_map_attendee_status(self):
        """Test _map_attendee_status maps Odoo states to iCalendar."""
        CalendarEvent = self.env["calendar.event"]
        self.assertEqual(CalendarEvent._map_attendee_status("accepted"), "ACCEPTED")
        self.assertEqual(CalendarEvent._map_attendee_status("declined"), "DECLINED")
        self.assertEqual(CalendarEvent._map_attendee_status("tentative"), "TENTATIVE")
        self.assertEqual(
            CalendarEvent._map_attendee_status("needsAction"), "NEEDS-ACTION"
        )
        self.assertEqual(CalendarEvent._map_attendee_status("unknown"), "NEEDS-ACTION")


@tagged("post_install", "-at_install")
class TestChangeDetection(TransactionCase, CaldavTestCommon):
    """Tests for change detection methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.users"].search([])._compute_is_caldav_enabled()
        cls.user_1_url = "https://mycaldav.test.com/test1calendar"
        cls.user_1 = cls._generate_user(
            "change_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url=cls.user_1_url,
        )

    def test_get_value_changes_no_change(self):
        """Test _get_value_changes returns empty when no changes."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Test Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        # Same values should return empty dict
        changes = event._get_value_changes({"name": "Test Event"})
        self.assertEqual(changes, {})

    def test_get_value_changes_with_change(self):
        """Test _get_value_changes detects changes."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Original Name",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        changes = event._get_value_changes({"name": "New Name"})
        self.assertIn("name", changes)
        self.assertEqual(changes["name"], "New Name")

    def test_get_recurrence_changes_no_recurrence(self):
        """Test _get_recurrence_changes with no recurrence."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Non-Recurring Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        # No recurrence vals and no recurrence_id should return empty
        changes = event._get_recurrence_changes({})
        self.assertEqual(changes, {})

    def test_get_recurrence_changes_adding_recurrence(self):
        """Test _get_recurrence_changes when adding recurrence."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Non-Recurring Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        recurrency_vals = {
            "recurrency": True,
            "rrule_type": "weekly",
            "count": 5,
        }
        changes = event._get_recurrence_changes(recurrency_vals)
        # Should return the recurrency vals since event has no recurrence
        self.assertEqual(changes, recurrency_vals)

    def test_to_sync_filters_correctly(self):
        """Test _to_sync returns only events that should sync."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Sync Test Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        # Event should be in _to_sync since user is caldav enabled and it's a base event
        to_sync = event._to_sync()
        self.assertIn(event, to_sync)

    def test_to_sync_excludes_non_caldav_users(self):
        """Test _to_sync excludes events for non-CalDAV users."""
        non_caldav_user = self._generate_user("non_caldav_change")

        event = (
            self.env["calendar.event"]
            .with_context(caldav_no_sync=True)
            .with_user(non_caldav_user)
            .create(
                {
                    "name": "Non-Sync Event",
                    "start": datetime.now() + timedelta(days=1),
                    "stop": datetime.now() + timedelta(days=1, hours=1),
                    "partner_ids": [Command.set([non_caldav_user.partner_id.id])],
                }
            )
        )

        to_sync = event._to_sync()
        self.assertNotIn(event, to_sync)


@tagged("post_install", "-at_install")
class TestRRuleParsing(TransactionCase):
    """Tests for RRULE parsing functions."""

    def test_parse_rrule_string_weekly(self):
        """Test parsing a weekly RRULE string."""
        from ..models.calendar_event import _parse_rrule_string

        rrule_str = "RRULE:FREQ=WEEKLY;COUNT=5;BYDAY=MO"
        result = _parse_rrule_string(rrule_str)

        self.assertEqual(str(result["FREQ"]), "WEEKLY")
        self.assertEqual(result["COUNT"], 5)
        self.assertIn("BYDAY", result)

    def test_parse_rrule_string_daily_with_until(self):
        """Test parsing a daily RRULE with UNTIL date."""
        from ..models.calendar_event import _parse_rrule_string

        rrule_str = "RRULE:FREQ=DAILY;UNTIL=20251231T000000"
        result = _parse_rrule_string(rrule_str)

        self.assertEqual(str(result["FREQ"]), "DAILY")
        self.assertIn("UNTIL", result)

    def test_parse_rrule_string_monthly_with_interval(self):
        """Test parsing a monthly RRULE with interval."""
        from ..models.calendar_event import _parse_rrule_string

        rrule_str = "RRULE:FREQ=MONTHLY;INTERVAL=2;COUNT=6"
        result = _parse_rrule_string(rrule_str)

        self.assertEqual(str(result["FREQ"]), "MONTHLY")
        self.assertEqual(result["INTERVAL"], 2)
        self.assertEqual(result["COUNT"], 6)

    def test_parse_rrule_string_invalid(self):
        """Test parsing an invalid RRULE string returns empty dict."""
        from ..models.calendar_event import _parse_rrule_string

        result = _parse_rrule_string("NOT_AN_RRULE")
        self.assertEqual(result, {})

    def test_parse_rrule_string_with_bymonthday(self):
        """Test parsing RRULE with BYMONTHDAY."""
        from ..models.calendar_event import _parse_rrule_string

        rrule_str = "RRULE:FREQ=MONTHLY;BYMONTHDAY=15"
        result = _parse_rrule_string(rrule_str)

        self.assertEqual(str(result["FREQ"]), "MONTHLY")
        self.assertEqual(result["BYMONTHDAY"], 15)

    def test_parse_rrule_string_yearly(self):
        """Test parsing a yearly RRULE."""
        from ..models.calendar_event import _parse_rrule_string

        rrule_str = "RRULE:FREQ=YEARLY;BYMONTH=12;COUNT=10"
        result = _parse_rrule_string(rrule_str)

        self.assertEqual(str(result["FREQ"]), "YEARLY")
        self.assertEqual(result["BYMONTH"], 12)
        self.assertEqual(result["COUNT"], 10)

    def test_parse_rrule_string_until_date_only(self):
        """Test parsing RRULE with UNTIL as date only (no time component)."""
        from ..models.calendar_event import _parse_rrule_string

        rrule_str = "RRULE:FREQ=DAILY;UNTIL=20251231"
        result = _parse_rrule_string(rrule_str)

        self.assertEqual(str(result["FREQ"]), "DAILY")
        self.assertIn("UNTIL", result)

    def test_parse_rrule_string_multiple_values(self):
        """Test parsing RRULE with comma-separated values."""
        from ..models.calendar_event import _parse_rrule_string

        rrule_str = "RRULE:FREQ=MONTHLY;BYMONTHDAY=1,15"
        result = _parse_rrule_string(rrule_str)

        self.assertEqual(str(result["FREQ"]), "MONTHLY")
        self.assertEqual(result["BYMONTHDAY"], [1, 15])

    def test_parse_rrule_string_unknown_key(self):
        """Test parsing RRULE with unknown key returns value as-is."""
        from ..models.calendar_event import _parse_rrule_string

        rrule_str = "RRULE:FREQ=DAILY;UNKNOWNKEY=somevalue"
        result = _parse_rrule_string(rrule_str)

        self.assertEqual(str(result["FREQ"]), "DAILY")
        self.assertEqual(result["UNKNOWNKEY"], "somevalue")


@tagged("post_install", "-at_install")
class TestExtractVcalEmail(TransactionCase):
    """Tests for email extraction from vCalAddress."""

    def test_extract_vcal_email_mailto(self):
        """Test extracting email from MAILTO: format."""
        from ..models.calendar_event import _extract_vcal_email

        result = _extract_vcal_email("MAILTO:test@example.com")
        self.assertEqual(result, "test@example.com")

    def test_extract_vcal_email_with_name(self):
        """Test extracting email when name is included."""
        from ..models.calendar_event import _extract_vcal_email

        result = _extract_vcal_email("John Doe <john.doe@example.com>")
        self.assertEqual(result, "john.doe@example.com")

    def test_extract_vcal_email_uppercase(self):
        """Test email extraction with uppercase returns empty."""
        from ..models.calendar_event import _extract_vcal_email

        # The regex only matches lowercase, so uppercase emails don't match
        result = _extract_vcal_email("MAILTO:TEST@EXAMPLE.COM")
        self.assertEqual(result, "")

    def test_extract_vcal_email_invalid(self):
        """Test extracting from invalid format returns empty string."""
        from ..models.calendar_event import _extract_vcal_email

        result = _extract_vcal_email("not-an-email")
        self.assertEqual(result, "")


@tagged("post_install", "-at_install")
class TestCalendarEventHelpers(TransactionCase, CaldavTestCommon):
    """Tests for calendar event helper methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.users"].search([])._compute_is_caldav_enabled()
        cls.user_1_url = "https://mycaldav.test.com/test1calendar"
        cls.user_1 = cls._generate_user(
            "helper_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url=cls.user_1_url,
        )

    def test_text_to_html_conversion(self):
        """Test _text_to_html converts markdown to HTML."""
        CalendarEvent = self.env["calendar.event"]
        text = "This is **bold** text"
        result = CalendarEvent._text_to_html(text)
        self.assertIn("<strong>", result)
        self.assertIn("bold", result)

    def test_is_base_event_for_non_recurring(self):
        """Test is_base_event is True for non-recurring events."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Non-Recurring Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        self.assertTrue(event.is_base_event)

    def test_differs_from_base_event_for_base(self):
        """Test differs_from_base_event is False for base events."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Base Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        self.assertFalse(event.differs_from_base_event)

    def test_caldav_users_computed(self):
        """Test caldav_user_ids is computed correctly."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Test Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        self.assertIn(self.user_1, event.caldav_user_ids)

    def test_is_caldav_enabled_method(self):
        """Test _is_caldav_enabled returns correct value."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Test Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        self.assertTrue(event._is_caldav_enabled())


@tagged("post_install", "-at_install")
class TestGetExistingInstance(TransactionCase, CaldavTestCommon):
    """Tests for _get_existing_instance method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.users"].search([])._compute_is_caldav_enabled()
        cls.user_1_url = "https://mycaldav.test.com/test1calendar"
        cls.user_1 = cls._generate_user(
            "instance_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url=cls.user_1_url,
        )

    def test_get_existing_instance_non_recurring(self):
        """Test finding existing non-recurring event by UID."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Test Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        CalendarEvent = self.env["calendar.event"]
        found = CalendarEvent._get_existing_instance(event.caldav_uid, None)
        self.assertEqual(found, event)

    def test_get_existing_instance_not_found(self):
        """Test returns empty recordset when UID not found."""
        CalendarEvent = self.env["calendar.event"]
        found = CalendarEvent._get_existing_instance("non-existent-uid", None)
        self.assertFalse(found)


@tagged("post_install", "-at_install")
class TestGetIcalAttendeeEmails(TransactionCase):
    """Tests for _get_ical_attendee_emails method."""

    def test_get_ical_attendee_emails_single(self):
        """Test extracting single attendee email."""
        CalendarEvent = self.env["calendar.event"]
        mock_component = MagicMock()
        mock_component.get.return_value = "mailto:attendee@example.com"

        result = CalendarEvent._get_ical_attendee_emails(mock_component)
        self.assertEqual(result, ["attendee@example.com"])

    def test_get_ical_attendee_emails_multiple(self):
        """Test extracting multiple attendee emails."""
        CalendarEvent = self.env["calendar.event"]
        mock_component = MagicMock()
        mock_component.get.return_value = [
            "mailto:attendee1@example.com",
            "mailto:attendee2@example.com",
        ]

        result = CalendarEvent._get_ical_attendee_emails(mock_component)
        self.assertEqual(len(result), 2)
        self.assertIn("attendee1@example.com", result)
        self.assertIn("attendee2@example.com", result)

    def test_get_ical_attendee_emails_empty(self):
        """Test returns empty list when no attendees."""
        CalendarEvent = self.env["calendar.event"]
        mock_component = MagicMock()
        mock_component.get.return_value = []

        result = CalendarEvent._get_ical_attendee_emails(mock_component)
        self.assertEqual(result, [])


@tagged("post_install", "-at_install")
class TestRecomputeCaldavIds(TransactionCase, CaldavTestCommon):
    """Tests for _recompute_caldav_ids method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.users"].search([])._compute_is_caldav_enabled()
        cls.user_1_url = "https://mycaldav.test.com/test1calendar"
        cls.user_1 = cls._generate_user(
            "recompute_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url=cls.user_1_url,
        )

    def test_recompute_caldav_ids_generates_uid(self):
        """Test _recompute_caldav_ids generates a new UID for non-recurring events."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Test Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        # UID should be set
        self.assertTrue(event.caldav_uid)
        # Recurrence ID should be False for non-recurring
        self.assertFalse(event.caldav_recurrence_id)

    def test_recompute_caldav_ids_keeps_uid_with_context(self):
        """Test _recompute_caldav_ids keeps UID when caldav_keep_ids context is set."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Test Event",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        original_uid = event.caldav_uid

        # Recompute with caldav_keep_ids context
        event.with_context(caldav_keep_ids=True)._recompute_caldav_ids()

        # UID should remain the same
        self.assertEqual(event.caldav_uid, original_uid)
