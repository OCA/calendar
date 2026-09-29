# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from .common import TestPublicHolidayResourceCommon


class TestSyncAction(TestPublicHolidayResourceCommon):
    """Synchronisation is run from the public holiday template list."""

    def _drop_mirrors(self, line):
        self._mirrors(line).with_context(public_holiday_sync=True).unlink()

    def test_action_recreates_missing_time_off(self):
        line = self._create_line(date(self.year, 10, 3))
        self._drop_mirrors(line)
        self.holiday.action_sync_global_leaves()
        self.assertTrue(self._mirrors(line))

    def test_action_reports_what_it_did(self):
        line = self._create_line(date(self.year, 10, 3))
        expected = len(self._mirrors(line))
        self._drop_mirrors(line)
        result = self.holiday.action_sync_global_leaves()
        self.assertEqual(result["tag"], "display_notification")
        self.assertIn(f"{expected} created", result["params"]["message"])
        self.assertEqual(result["params"]["type"], "success")

    def test_action_warns_about_public_holidays_generating_nothing(self):
        foreign = self.holiday_model.create(
            {"year": self.year, "country_id": self.other_country.id}
        )
        self._create_line(date(self.year, 7, 14), name="Bastille", holiday=foreign)
        result = foreign.action_sync_global_leaves()
        self.assertEqual(result["params"]["type"], "warning")
        self.assertTrue(result["params"]["sticky"])

    def test_action_on_an_empty_calendar(self):
        result = self.holiday.action_sync_global_leaves()
        self.assertIn("no public holiday", result["params"]["message"].lower())

    def test_action_covers_every_selected_calendar(self):
        other = self.holiday_model.create(
            {"year": self.year, "country_id": self.other_country.id}
        )
        line = self._create_line(date(self.year, 10, 3))
        self._drop_mirrors(line)
        (self.holiday | other).action_sync_global_leaves()
        self.assertTrue(self._mirrors(line))

    def test_server_action_is_bound_to_the_list(self):
        action = self.env.ref(
            "calendar_public_holiday_resource.action_sync_public_holidays"
        )
        self.assertEqual(
            action.binding_model_id,
            self.env.ref("calendar_public_holiday.model_calendar_public_holiday"),
        )
        self.assertIn("list", action.binding_view_types)

    def test_server_action_runs(self):
        line = self._create_line(date(self.year, 10, 3))
        self._drop_mirrors(line)
        action = self.env.ref(
            "calendar_public_holiday_resource.action_sync_public_holidays"
        )
        action.with_context(
            active_model="calendar.public.holiday",
            active_ids=self.holiday.ids,
            active_id=self.holiday.id,
        ).run()
        self.assertTrue(self._mirrors(line))
