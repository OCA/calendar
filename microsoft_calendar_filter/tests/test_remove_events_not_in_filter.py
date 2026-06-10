# Copyright 2026 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date, datetime
from unittest.mock import ANY, patch

from odoo.addons.microsoft_calendar.models.res_users import User
from odoo.addons.microsoft_calendar.tests.common import (
    TestCommon,
    mock_get_token,
    patch_api,
)
from odoo.addons.microsoft_calendar.utils.microsoft_calendar import (
    MicrosoftCalendarService,
)

from ..models.res_config_settings import FILTER_ODOO_EVENTS


@patch.object(User, "_get_microsoft_calendar_token", mock_get_token)
class TestRemoveEventsNotInFilter(TestCommon):
    @patch_api
    def setUp(self):
        super(TestRemoveEventsNotInFilter, self).setUp()
        self.ICP = self.env["ir.config_parameter"].sudo()
        self.create_events_for_tests()
        res_model_id = self.env["ir.model"]._get_id("res.partner")
        year = date.today().year
        self.simple_event.write(
            {
                "res_model_id": res_model_id,
                "res_model": "res.partner",
                "res_id": self.organizer_user.partner_id.id,
                "start": datetime(year, 1, 15, 8, 0),
                "stop": datetime(year, 1, 15, 18, 0),
            }
        )

    @patch.object(MicrosoftCalendarService, "delete")
    def test_delete_simple_event_from_odoo_organizer_calendar(self, mock_delete):
        # We now define to exclude res.partner related events from synchronization.
        self.ICP.set_param(
            FILTER_ODOO_EVENTS,
            "[('res_model', '!=', 'res.partner')]",
        )
        event_id = self.simple_event.ms_organizer_event_id
        # Now remove the event that no longer satisfies the filter.
        self.simple_event.with_user(self.organizer_user)._remove_events_not_in_filter()
        self.assertFalse(self.simple_event.microsoft_id)
        mock_delete.assert_called_once_with(
            event_id, token=mock_get_token(self.organizer_user), timeout=ANY
        )
