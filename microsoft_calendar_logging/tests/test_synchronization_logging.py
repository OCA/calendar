# Copyright 2025 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import ANY, patch

from freezegun import freeze_time

from odoo.addons.microsoft_account.models.microsoft_service import MicrosoftService
from odoo.addons.microsoft_calendar.models.res_users import User
from odoo.addons.microsoft_calendar.tests.common import (
    TestCommon,
    _modified_date_in_the_future,
    mock_get_token,
)
from odoo.addons.microsoft_calendar.utils.event_id_storage import combine_ids
from odoo.addons.microsoft_calendar.utils.microsoft_calendar import (
    MicrosoftCalendarService,
)
from odoo.addons.microsoft_calendar.utils.microsoft_event import MicrosoftEvent


@patch.object(User, "_get_microsoft_calendar_token", mock_get_token)
class TestSynchronizationLogging(TestCommon):
    @freeze_time("2021-09-22")
    def test_microsoft2odoo(self):
        expected_event = dict(self.expected_odoo_event_from_outlook, user_id=False)
        new_record = self._get_new_record_from_microsoft()
        self.assertEqual(len(new_record), 1)
        self.assertTrue(new_record.created_by_synchronization)
        self.assert_odoo_event(new_record, expected_event)
        # Modify the event.
        modified_event = self._get_modifield_event(new_record)
        self._synchronize_events(modified_event)
        new_record.invalidate_recordset(["datetime_updated_from_microsoft"])
        self.assertTrue(new_record.datetime_updated_from_microsoft)  # Should be set
        self.assertEqual(new_record.name, "Update simple event")

    @freeze_time("2021-09-22")
    @patch.object(MicrosoftService, "_do_request")
    def test_odoo2microsoft_create(self, mock_do_request):
        Calendar = self.env["calendar.event"]
        oca_days = Calendar.create(
            {
                "name": "OCA Days",
                "description": "<p>OCA Days</p>",
                "location": "Luik/Liège",
                "active": True,
                "start": self.start_date,
                "stop": self.end_date,
                "user_id": self.organizer_user.id,
                "partner_ids": [
                    self.organizer_user.partner_id.id,
                    self.attendee_user.partner_id.id,
                ],
            }
        )
        self.assertFalse(oca_days.created_by_synchronization)
        mock_do_request.return_value = (200, {"id": 1, "iCalUId": 2}, None)
        oca_days._sync_odoo2microsoft()
        self.assertTrue(oca_days.datetime_created_on_microsoft)  # Should be set

    @freeze_time("2021-09-22")
    @patch.object(MicrosoftService, "_do_request")
    def test_odoo2microsoft_update(self, mock_do_request):
        # We test with an odoo event that is created from a
        # microsoft event, because for a succesfull update a
        # microsoft_id is required. Normall when an event is
        # created on Odoo, it is first send to MS. Then in the
        # next synchronization, the microsoft_id will be retrieved
        # and the Odoo event updated with its value.
        oca_days = self._get_new_record_from_microsoft()
        self.assertEqual(len(oca_days), 1)
        oca_days.write({"name": "The Great OCA Days"})
        self.assertTrue(oca_days.need_sync_m)
        mock_do_request.return_value = (200, True, None)
        oca_days.with_user(self.organizer_user)._sync_odoo2microsoft()
        self.assertTrue(oca_days.datetime_updated_on_microsoft)  # Should be set

    def _get_new_record_from_microsoft(self):
        """Create a record from microsoft event."""
        Calendar = self.env["calendar.event"]
        existing_records = Calendar.search([])
        microsoft_events = self._get_test_events()
        self._synchronize_events(microsoft_events)
        # We should have a new event.
        records = Calendar.search([])
        new_record = records - existing_records
        return new_record

    @patch.object(MicrosoftCalendarService, "get_events")
    def _synchronize_events(self, microsoft_events, mock_get_events):
        """Synchronize the given MS events."""
        mock_get_events.return_value = (microsoft_events, None)
        self.organizer_user.with_user(
            self.organizer_user
        ).sudo()._sync_microsoft_calendar()

    def _get_test_events(self):
        public_event_data = self._get_public_event_data()
        return MicrosoftEvent([public_event_data])

    def _get_public_event_data(self):
        return dict(
            self.simple_event_from_outlook_attendee,
            organizer={
                "emailAddress": {"address": "john.doe@odoo.com", "name": "John Doe"},
            },
        )

    def _get_modifield_event(self, odoo_event):
        modified_data = dict(
            self._get_public_event_data(),
            subject="Update simple event",
            lastModifiedDateTime=_modified_date_in_the_future(odoo_event),
        )
        return MicrosoftEvent([modified_data])

    @patch.object(MicrosoftCalendarService, "delete")
    def test_delete_simple_event_from_odoo_organizer_calendar(self, mock_delete):
        # Copied (modified) from Odoo to check delete still works.
        simple_event = self._get_simple_event()
        event_id = simple_event.ms_organizer_event_id
        simple_event.with_user(self.organizer_user).unlink()
        self.call_post_commit_hooks()
        simple_event.invalidate_recordset()
        self.assertFalse(simple_event.exists())
        mock_delete.assert_called_once_with(
            event_id, token=mock_get_token(self.organizer_user), timeout=ANY
        )

    @patch.object(MicrosoftCalendarService, "get_events")
    def test_cancel_simple_event_from_outlook_organizer_calendar(self, mock_get_events):
        # Copied (modified) from Odoo to check delete still works.
        simple_event = self._get_simple_event()
        event_id = simple_event.ms_organizer_event_id
        mock_get_events.return_value = (
            MicrosoftEvent([{"id": event_id, "@removed": {"reason": "deleted"}}]),
            None,
        )
        self.organizer_user.with_user(
            self.organizer_user
        ).sudo()._sync_microsoft_calendar()
        self.assertFalse(simple_event.exists())

    def _get_simple_event(self):
        Calendar = self.env["calendar.event"]
        simple_event = Calendar.search(
            [("name", "=", "simple_event")]
        ) or Calendar.with_user(self.organizer_user).create(
            dict(
                self.simple_event_values,
                microsoft_id=combine_ids("123", "456"),
            )
        )
        return simple_event
