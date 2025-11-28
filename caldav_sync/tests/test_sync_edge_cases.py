"""Additional tests to increase code coverage for caldav_sync module.

These tests target specific code paths that were not covered by existing tests.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from icalendar import vRecur

from odoo import Command
from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import mute_logger

from .common import CaldavTestCommon


@tagged("post_install", "-at_install")
class TestCalendarAttendeeNotifications(TransactionCase, CaldavTestCommon):
    """Tests for calendar.attendee notification suppression."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "attendee_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )

    def test_send_mail_to_attendees_with_dont_notify_context(self):
        """Test that _send_mail_to_attendees returns False with dont_notify context."""
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

        attendee = event.attendee_ids[:1]
        if attendee:
            mail_template = self.env.ref(
                "calendar.calendar_template_meeting_invitation"
            )
            # With dont_notify context, should return False
            result = attendee.with_context(dont_notify=True)._send_mail_to_attendees(
                mail_template
            )
            self.assertFalse(result)

    def test_send_mail_to_attendees_without_dont_notify_context(self):
        """Test that _send_mail_to_attendees calls super without dont_notify."""
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

        attendee = event.attendee_ids[:1]
        if attendee:
            mail_template = self.env.ref(
                "calendar.calendar_template_meeting_invitation"
            )
            # Without dont_notify context, should call super (may return various values)
            # We just verify it doesn't raise an error
            attendee._send_mail_to_attendees(mail_template)


@tagged("post_install", "-at_install")
class TestGetRecurrencyValuesFromIcal(TransactionCase, CaldavTestCommon):
    """Tests for _get_recurrency_values_from_ical_event method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.CalendarEvent = cls.env["calendar.event"]

    def test_recurrency_values_with_recurrence_id_not_following(self):
        """Test component with recurrence-id that doesn't follow recurrence."""
        mock_recurrence_id = MagicMock()
        mock_recurrence_id.dt = datetime(2025, 1, 15, 10, 0, 0)

        mock_dtstart = MagicMock()
        mock_dtstart.dt = datetime(2025, 1, 15, 11, 0, 0)  # Different time

        mock_component = MagicMock()
        mock_component.get.side_effect = lambda key, default=None: {
            "recurrence-id": mock_recurrence_id,
            "dtstart": mock_dtstart,
        }.get(key, default)
        mock_component.property_items.return_value = []

        result = self.CalendarEvent._get_recurrency_values_from_ical_event(
            mock_component
        )

        self.assertEqual(result.get("follow_recurrence"), False)
        self.assertEqual(result.get("recurrence_update"), "self_only")

    def test_recurrency_values_with_recurrence_id_following_no_rrule(self):
        """Test component with recurrence-id following recurrence but no RRULE."""
        mock_recurrence_id = MagicMock()
        mock_recurrence_id.dt = datetime(2025, 1, 15, 10, 0, 0)

        mock_dtstart = MagicMock()
        mock_dtstart.dt = datetime(2025, 1, 15, 10, 0, 0)  # Same time

        mock_component = MagicMock()
        mock_component.get.side_effect = lambda key, default=None: {
            "recurrence-id": mock_recurrence_id,
            "dtstart": mock_dtstart,
        }.get(key, default)
        mock_component.property_items.return_value = []

        result = self.CalendarEvent._get_recurrency_values_from_ical_event(
            mock_component
        )

        self.assertEqual(result.get("follow_recurrence"), True)
        self.assertEqual(result.get("recurrence_update"), "self_only")

    def test_recurrency_values_with_forever_end_type(self):
        """Test RRULE with no COUNT or UNTIL (forever) gets converted."""
        rrule = vRecur({"FREQ": "DAILY"})

        mock_dtstart = MagicMock()
        mock_dtstart.dt = datetime(2025, 1, 15, 10, 0, 0)

        mock_component = MagicMock()
        mock_component.get.side_effect = lambda key, default=None: {
            "dtstart": mock_dtstart,
        }.get(key, default)
        mock_component.property_items.return_value = [("RRULE", rrule)]
        mock_component.decoded = lambda key: mock_dtstart.dt

        result = self.CalendarEvent._get_recurrency_values_from_ical_event(
            mock_component
        )

        # Forever should be converted to count
        self.assertEqual(result.get("end_type"), "count")

    def test_recurrency_values_with_until_as_list(self):
        """Test RRULE with UNTIL as a list (edge case)."""
        from pytz import utc

        until_dt = datetime(2025, 12, 31, 0, 0, 0, tzinfo=utc)
        rrule = vRecur({"FREQ": "WEEKLY", "UNTIL": [until_dt]})

        mock_dtstart = MagicMock()
        mock_dtstart.dt = datetime(2025, 1, 15, 10, 0, 0, tzinfo=utc)

        mock_component = MagicMock()
        mock_component.get.side_effect = lambda key, default=None: {
            "dtstart": mock_dtstart,
        }.get(key, default)
        mock_component.property_items.return_value = [("RRULE", rrule)]
        mock_component.decoded = lambda key: mock_dtstart.dt

        result = self.CalendarEvent._get_recurrency_values_from_ical_event(
            mock_component
        )

        self.assertTrue(result.get("recurrency"))


@tagged("post_install", "-at_install")
class TestGetRecurrenceChanges(TransactionCase, CaldavTestCommon):
    """Tests for _get_recurrence_changes method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "rec_change_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )

    def test_recurrence_changes_no_recurrence_no_vals(self):
        """Test _get_recurrence_changes returns empty when no recurrence and no vals."""
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

        # No recurrence_id and empty vals should return empty dict
        changes = event._get_recurrence_changes({})
        self.assertEqual(changes, {})

    def test_recurrence_changes_adding_recurrence(self):
        """
        Test _get_recurrence_changes when adding recurrence to
        non-recurring event.
        """
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

        # Adding recurrence vals to non-recurring event should return the vals
        recurrency_vals = {
            "recurrency": True,
            "rrule_type": "daily",
            "count": 3,
        }
        changes = event._get_recurrence_changes(recurrency_vals)
        self.assertEqual(changes, recurrency_vals)


@tagged("post_install", "-at_install")
class TestGetValueChanges(TransactionCase, CaldavTestCommon):
    """Tests for _get_value_changes method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "val_change_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )

    def test_value_changes_partner_ids_no_change(self):
        """Test _get_value_changes with same partner_ids returns no change."""
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

        # Same partner_ids should not show as changed
        values = {"partner_ids": [(6, 0, [self.user_1.partner_id.id])]}
        changes = event._get_value_changes(values)
        self.assertNotIn("partner_ids", changes)

    def test_value_changes_partner_ids_with_change(self):
        """Test _get_value_changes detects partner_ids changes."""
        partner2 = self.env["res.partner"].create(
            {"name": "New Partner", "email": "new@example.com"}
        )

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

        # Adding a partner should show as changed
        values = {"partner_ids": [(6, 0, [self.user_1.partner_id.id, partner2.id])]}
        changes = event._get_value_changes(values)
        self.assertIn("partner_ids", changes)

    def test_value_changes_with_many2one_field(self):
        """Test _get_value_changes handles Many2one fields correctly."""
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

        # user_id is a Many2one field
        values = {"user_id": self.user_1.id}
        changes = event._get_value_changes(values)
        # Should not show as changed if same
        self.assertNotIn("user_id", changes)


@tagged("post_install", "-at_install")
class TestGetOutdated(TransactionCase, CaldavTestCommon):
    """Tests for _get_outdated method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "outdated_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )
        cls.CalendarEvent = cls.env["calendar.event"]

    def test_get_outdated_no_existing_instance(self):
        """Test _get_outdated returns False when no existing instance."""
        mock_component = MagicMock()
        mock_component.get.return_value = None

        result = self.CalendarEvent._get_outdated(
            mock_component, self.CalendarEvent, self.CalendarEvent
        )
        self.assertFalse(result)

    def test_get_outdated_no_dtstamp(self):
        """Test _get_outdated returns False when no dtstamp."""
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

        mock_component = MagicMock()
        mock_component.get.return_value = None

        result = self.CalendarEvent._get_outdated(
            mock_component, event, self.CalendarEvent
        )
        self.assertFalse(result)

    def test_get_outdated_already_synced(self):
        """Test _get_outdated returns False when event already in synced_events."""
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

        mock_dtstamp = MagicMock()
        mock_dtstamp.dt = datetime.now()
        mock_component = MagicMock()
        mock_component.get.return_value = mock_dtstamp

        # Event is in synced_events
        result = self.CalendarEvent._get_outdated(mock_component, event, event)
        self.assertFalse(result)

    def test_get_outdated_naive_dtstamp(self):
        """Test _get_outdated handles naive datetime in dtstamp."""
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

        # Use a naive datetime (no timezone)
        mock_dtstamp = MagicMock()
        mock_dtstamp.dt = datetime.now() - timedelta(days=1)  # Older than write_date
        mock_component = MagicMock()
        mock_component.get.return_value = mock_dtstamp

        result = self.CalendarEvent._get_outdated(
            mock_component, event, self.CalendarEvent
        )
        self.assertTrue(result)


@tagged("post_install", "-at_install")
class TestGetAttendeePartners(TransactionCase, CaldavTestCommon):
    """Tests for _get_attendee_partners method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "attendee_partner_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )
        cls.CalendarEvent = cls.env["calendar.event"]

    def test_get_attendee_partners_creates_missing(self):
        """Test _get_attendee_partners creates partners for unknown emails."""
        mock_component = MagicMock()
        mock_component.get.side_effect = lambda key, default=[]: {
            "attendee": ["mailto:newattendee@example.com"],
            "organizer": None,
        }.get(key, default)

        # Make sure the partner doesn't exist
        existing = self.env["res.partner"].search(
            [("email", "=", "newattendee@example.com")]
        )
        existing.unlink()

        partners = self.CalendarEvent._get_attendee_partners(
            mock_component, self.user_1.partner_id.email
        )

        # Should have created the partner
        new_partner = self.env["res.partner"].search(
            [("email", "=", "newattendee@example.com")]
        )
        self.assertTrue(new_partner)
        self.assertIn(new_partner, partners)

    def test_get_attendee_partners_adds_organizer(self):
        """Test _get_attendee_partners adds organizer to attendees."""
        mock_component = MagicMock()
        mock_component.get.side_effect = lambda key, default=[]: {
            "attendee": [],
            "organizer": "mailto:organizer@example.com",
        }.get(key, default)

        # Create the organizer partner
        organizer = self.env["res.partner"].create(
            {"name": "Organizer", "email": "organizer@example.com"}
        )

        partners = self.CalendarEvent._get_attendee_partners(
            mock_component, self.user_1.partner_id.email
        )

        self.assertIn(organizer, partners)

    def test_get_attendee_partners_deduplicates_by_email(self):
        """Test _get_attendee_partners deduplicates partners with same email."""
        # Create two partners with the same email
        email = "duplicate@example.com"
        self.env["res.partner"].create({"name": "Partner 1", "email": email})
        self.env["res.partner"].create({"name": "Partner 2", "email": email})

        mock_component = MagicMock()
        mock_component.get.side_effect = lambda key, default=[]: {
            "attendee": [f"mailto:{email}"],
            "organizer": None,
        }.get(key, default)

        partners = self.CalendarEvent._get_attendee_partners(
            mock_component, self.user_1.partner_id.email
        )

        # Should only have one partner with that email
        partners_with_email = partners.filtered(lambda p: p.email == email)
        self.assertEqual(len(partners_with_email), 1)


@tagged("post_install", "-at_install")
class TestGetOrganizerPartner(TransactionCase, CaldavTestCommon):
    """Tests for _get_organizer_partner method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.CalendarEvent = cls.env["calendar.event"]

    def test_get_organizer_partner_creates_new(self):
        """Test _get_organizer_partner creates partner if not exists."""
        email = "neworganizer@example.com"

        # Make sure the partner doesn't exist
        existing = self.env["res.partner"].search([("email", "=", email)])
        existing.unlink()

        mock_component = MagicMock()
        mock_component.get.return_value = f"mailto:{email}"

        partner = self.CalendarEvent._get_organizer_partner(mock_component)

        self.assertTrue(partner)
        self.assertEqual(partner.email, email)

    def test_get_organizer_partner_finds_existing(self):
        """Test _get_organizer_partner finds existing partner."""
        email = "existingorganizer@example.com"
        existing_partner = self.env["res.partner"].create(
            {"name": "Existing Organizer", "email": email}
        )

        mock_component = MagicMock()
        mock_component.get.return_value = f"mailto:{email}"

        partner = self.CalendarEvent._get_organizer_partner(mock_component)

        self.assertEqual(partner, existing_partner)

    def test_get_organizer_partner_no_organizer(self):
        """Test _get_organizer_partner returns empty when no organizer."""
        mock_component = MagicMock()
        mock_component.get.return_value = None

        partner = self.CalendarEvent._get_organizer_partner(mock_component)

        self.assertFalse(partner)


@tagged("post_install", "-at_install")
class TestExtractComponentText(TransactionCase):
    """Tests for _extract_component_text method."""

    def test_extract_component_text_with_value(self):
        """Test extracting text from component with value."""
        CalendarEvent = self.env["calendar.event"]
        mock_component = MagicMock()
        mock_component.get.return_value = "Test Description"

        result = CalendarEvent._extract_component_text(mock_component, "description")
        self.assertEqual(result, "Test Description")

    def test_extract_component_text_empty(self):
        """Test extracting text from component with no value."""
        CalendarEvent = self.env["calendar.event"]
        mock_component = MagicMock()
        mock_component.get.return_value = None

        result = CalendarEvent._extract_component_text(mock_component, "description")
        self.assertEqual(result, "")


@tagged("post_install", "-at_install")
class TestSyncWriteToCaldav(TransactionCase, CaldavTestCommon):
    """Tests for _sync_write_to_caldav method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "sync_write_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )

    def test_sync_write_base_event_not_found(self):
        """Test _sync_write_to_caldav handles missing base event gracefully."""
        with patch("caldav.DAVClient") as MockDAVClient:
            mock_client = MockDAVClient.return_value
            mock_calendar = MagicMock()
            mock_client.calendar.return_value = mock_calendar
            mock_calendar.events.return_value = []  # No events on server

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

            # This should not raise an error even though base event isn't found
            event._sync_write_to_caldav()


@tagged("post_install", "-at_install")
class TestSyncUnlinkToCaldav(TransactionCase, CaldavTestCommon):
    """Tests for _sync_unlink_to_caldav method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "sync_unlink_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )

    def test_sync_unlink_event_not_found(self):
        """Test _sync_unlink_to_caldav handles NotFoundError gracefully."""
        from caldav.lib.error import NotFoundError

        with patch("caldav.DAVClient") as MockDAVClient:
            mock_client = MockDAVClient.return_value
            mock_calendar = MagicMock()
            mock_client.calendar.return_value = mock_calendar
            mock_calendar.event_by_uid.side_effect = NotFoundError("Not found")

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

            # This should not raise an error
            event._sync_unlink_to_caldav()

    def test_sync_unlink_with_caldav_delete_all_context(self):
        """Test _sync_unlink_to_caldav with caldav_delete_all context."""
        with patch("caldav.DAVClient") as MockDAVClient:
            mock_client = MockDAVClient.return_value
            mock_calendar = MagicMock()
            mock_client.calendar.return_value = mock_calendar
            mock_caldav_event = MagicMock()
            mock_calendar.event_by_uid.return_value = mock_caldav_event

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

            # With caldav_delete_all, should delete the whole event
            event.with_context(caldav_delete_all=True)._sync_unlink_to_caldav()
            mock_caldav_event.delete.assert_called_once()


@tagged("post_install", "-at_install")
class TestMatchesCaldavStart(TransactionCase, CaldavTestCommon):
    """Tests for _matches_caldav_start method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "matches_start_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )

    def test_matches_caldav_start_with_timezone(self):
        """Test _matches_caldav_start with timezone-aware caldav event."""
        from pytz import utc

        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            start = datetime(2025, 2, 1, 10, 0, 0)
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Test Event",
                        "start": start,
                        "stop": start + timedelta(hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        mock_dtstart = MagicMock()
        mock_dtstart.dt = utc.localize(start)
        mock_component = MagicMock()
        mock_component.get.return_value = mock_dtstart
        mock_caldav_event = MagicMock()
        mock_caldav_event.icalendar_component = mock_component

        result = event._matches_caldav_start(mock_caldav_event)
        self.assertTrue(result)

    def test_matches_caldav_start_naive_datetime(self):
        """Test _matches_caldav_start with naive datetime."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            start = datetime(2025, 2, 1, 10, 0, 0)
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Test Event",
                        "start": start,
                        "stop": start + timedelta(hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                    }
                )
            )

        # Create a proper naive datetime mock
        mock_dtstart = MagicMock()
        mock_dtstart.dt = start  # Naive datetime (no tzinfo)
        mock_component = MagicMock()
        mock_component.get.return_value = mock_dtstart
        mock_caldav_event = MagicMock()
        mock_caldav_event.icalendar_component = mock_component

        result = event._matches_caldav_start(mock_caldav_event)
        self.assertTrue(result)


@tagged("post_install", "-at_install")
class TestWriteArchivesEvent(TransactionCase, CaldavTestCommon):
    """Tests for write method when archiving events."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "archive_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )

    def test_write_archives_event_syncs_unlink(self):
        """Test that archiving an event (active=False) calls _sync_unlink_to_caldav."""
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

        # Patch _sync_unlink_to_caldav to verify it gets called
        with patch.object(type(event), "_sync_unlink_to_caldav") as mock_sync_unlink:
            # Archive the event
            event.with_context(caldav_no_sync=False).write({"active": False})

            # Should have called _sync_unlink_to_caldav
            mock_sync_unlink.assert_called()


@tagged("post_install", "-at_install")
class TestSyncCreateException(TransactionCase, CaldavTestCommon):
    """Tests for exception handling in _sync_create_to_caldav."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "sync_create_exc_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )

    def test_sync_create_handles_exception(self):
        """Test _sync_create_to_caldav handles exceptions gracefully."""
        with patch("caldav.DAVClient") as MockDAVClient:
            mock_client = MockDAVClient.return_value
            mock_calendar = MagicMock()
            mock_client.calendar.return_value = mock_calendar
            # Make save_event raise an exception
            mock_calendar.save_event.side_effect = Exception("Connection failed")

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

            # Mute expected error log
            with mute_logger("odoo.addons.caldav_sync"):
                # This should not raise an error
                event._sync_create_to_caldav()


@tagged("post_install", "-at_install")
class TestUnlinkException(TransactionCase, CaldavTestCommon):
    """Tests for exception handling in unlink."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "unlink_exc_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )

    def test_unlink_handles_exception(self):
        """Test unlink handles exceptions in _sync_unlink_to_caldav gracefully."""
        with patch("caldav.DAVClient") as MockDAVClient:
            mock_client = MockDAVClient.return_value
            mock_calendar = MagicMock()
            mock_client.calendar.return_value = mock_calendar
            # Make event_by_uid raise an exception
            mock_calendar.event_by_uid.side_effect = Exception("Connection failed")

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
                        "caldav_uid": "test-uid-789",
                    }
                )
            )

            # Mute expected error log
            with mute_logger("odoo.addons.caldav_sync"):
                # This should not raise an error - exception should be caught
                event.with_context(caldav_no_sync=False).unlink()


@tagged("post_install", "-at_install")
class TestCreateEventData(TransactionCase, CaldavTestCommon):
    """Tests for _create_event_data and related methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "event_data_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )

    def test_create_event_data_with_videocall_location(self):
        """Test _create_event_data includes videocall_location."""
        with patch("caldav.DAVClient"):
            self.user_1._compute_is_caldav_enabled()
            event = (
                self.env["calendar.event"]
                .with_context(caldav_no_sync=True)
                .with_user(self.user_1)
                .create(
                    {
                        "name": "Video Call Meeting",
                        "start": datetime.now() + timedelta(days=1),
                        "stop": datetime.now() + timedelta(days=1, hours=1),
                        "partner_ids": [Command.set([self.user_1.partner_id.id])],
                        "videocall_location": "https://meet.example.com/abc123",
                    }
                )
            )
            event_data = event._create_event_data()
            self.assertIn("conference", event_data)
            self.assertEqual(
                event_data["conference"], "https://meet.example.com/abc123"
            )


@tagged("post_install", "-at_install")
class TestUpdateBaseCaldavEvent(TransactionCase, CaldavTestCommon):
    """Tests for _update_base_caldav_event method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls._generate_user(
            "update_base_test1",
            caldav_username="user1",
            caldav_password="pass1",
            caldav_url="https://mycaldav.test.com/test1calendar",
        )

    def test_update_base_caldav_event_no_existing_event(self):
        """Test _update_base_caldav_event creates event when none exists."""
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
            mock_calendar = MagicMock()
            event_data = {"summary": "Test Event"}
            # Call with None event - should call add_event
            event._update_base_caldav_event(mock_calendar, None, event_data)
            mock_calendar.add_event.assert_called_once()
