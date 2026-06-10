# Copyright 2025-2026 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import patch

from odoo.addons.microsoft_calendar.models.res_users import User
from odoo.addons.microsoft_calendar.tests.common import TestCommon, mock_get_token
from odoo.addons.microsoft_calendar.utils.microsoft_event import MicrosoftEvent

from ..models.res_config_settings import FILTER_PRIVATE_EVENTS


@patch.object(User, "_get_microsoft_calendar_token", mock_get_token)
class TestFilterPrivateEvents(TestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ICP = cls.env["ir.config_parameter"].sudo()
        ICP.set_param(FILTER_PRIVATE_EVENTS, True)

    def test_filter_private_events(self):
        """Test private events are not created in Odoo from Outlook."""
        Calendar = self.env["calendar.event"]
        existing_records = Calendar.search([])
        expected_event = dict(self.expected_odoo_event_from_outlook, user_id=False)
        microsoft_events = self._get_public_and_private_event()
        Calendar.with_user(self.organizer_user)._sync_microsoft2odoo(microsoft_events)
        # Only the public event should have been synchronized.
        records = Calendar.search([])
        new_records = records - existing_records
        self.assertEqual(len(new_records), 1)
        self.assertEqual(new_records.privacy, "public")
        self.assert_odoo_event(new_records, expected_event)

    def test_remove_ms_private_events(self):
        """Test public MS event that becomes private will be deleted."""
        Calendar = self.env["calendar.event"]
        existing_records = Calendar.search([])
        public_event_dict = self._get_public_event()
        microsoft_events = MicrosoftEvent([public_event_dict])
        Calendar.with_user(self.organizer_user)._sync_microsoft2odoo(microsoft_events)
        records = Calendar.search([])
        new_records = records - existing_records
        self.assertEqual(len(new_records), 1)
        self.assertEqual(new_records.privacy, "public")
        # Make the public event private and test removal
        to_be_removed_id = new_records.id
        public_event_dict["sensitivity"] = "private"
        microsoft_events = MicrosoftEvent([public_event_dict])
        Calendar.with_user(self.organizer_user)._sync_microsoft2odoo(microsoft_events)
        # The record should have been removed now.
        record_still_there = Calendar.search([("id", "=", to_be_removed_id)])
        self.assertEqual(len(record_still_there), 0)

    def test_filter_events(self):
        CalendarSync = self.env["microsoft.calendar.sync"]
        microsoft_events = self._get_public_and_private_event()
        filtered_events = CalendarSync._filter_microsoft_events(microsoft_events)
        ms_events = [event for event in filtered_events]
        self.assertEqual(len(ms_events), 1)
        self.assertEqual(ms_events[0].iCalUId, "456")
        self.assertEqual(ms_events[0].sensitivity, "normal")

    def _get_public_and_private_event(self):
        public_event = self._get_public_event()
        private_event = self._get_private_event()
        return MicrosoftEvent([public_event, private_event])

    def _get_public_event(self):
        return dict(
            self.simple_event_from_outlook_attendee,
            organizer={
                "emailAddress": {"address": "john.doe@odoo.com", "name": "John Doe"},
            },
        )

    def _get_private_event(self):
        return dict(
            self.simple_event_from_outlook_attendee,
            id="789",
            iCalUId="987",
            organizer={
                "emailAddress": {
                    "address": "rosa.luxemburg@spartakus.de",
                    "name": "Rosa Luxemburg",
                },
            },
            sensitivity="private",
        )
