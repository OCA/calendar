# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo_test_helper import FakeModelLoader

from odoo.tests import common


class TestCalendarEventLinkMixin(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        from .calendar_event_link_tester import CalendarEventLinkTester

        cls.loader.update_registry((CalendarEventLinkTester,))
        cls.test_model = cls.env["calendar.event.link.tester"]
        cls.record = cls.test_model.create({"name": "Test Record"})

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        return super().tearDownClass()

    def test_calendar_event_link(self):
        self.assertEqual(self.record.event_count, 0)

        event_model = self.env["calendar.event"]
        now = datetime.now()
        event_model.create(
            [
                {
                    "name": "Meeting 1",
                    "res_model": self.record._name,
                    "res_id": self.record.id,
                    "start": now,
                    "stop": now,
                },
                {
                    "name": "Meeting 2",
                    "res_model": self.record._name,
                    "res_id": self.record.id,
                    "start": now,
                    "stop": now,
                },
            ]
        )

        self.record._compute_event_count()
        self.assertEqual(self.record.event_count, 2)

        action = self.record.action_show_events()
        self.assertEqual(action["res_model"], "calendar.event")
        self.assertEqual(
            action["domain"],
            [("res_model", "=", self.record._name), ("res_id", "=", self.record.id)],
        )
        self.assertEqual(action["context"]["default_res_id"], self.record.id)
        self.assertEqual(action["context"]["default_res_model"], self.record._name)
        self.assertEqual(action["context"]["default_name"], self.record.display_name)
