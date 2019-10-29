# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestCalendarEventLink(TransactionCase):
    def setUp(self):
        super(TestCalendarEventLink, self).setUp()
        self.task = self.env["project.task"].search([], limit=1)

    def test_calendar_event_link(self):
        calendar_event_link_action = self.task.action_show_events()
        event = (
            self.env["calendar.event"]
            .with_context(calendar_event_link_action["context"])
            .create(
                {
                    "name": "event",
                    "start": "2019-10-29 10:00:00",
                    "stop": "2019-10-29 11:00:00",
                }
            )
        )
        self.assertEqual(self.task.event_count, 1)
        self.assertEqual(
            self.env["calendar.event"].search(calendar_event_link_action["domain"]),
            event,
        )
