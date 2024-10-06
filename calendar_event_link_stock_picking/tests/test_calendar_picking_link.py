# Copyright 2019 ACSONE SA/NV
# Copyright 2024 INVITU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestCalendarPickingLink(TransactionCase):
    def setUp(self):
        super(TestCalendarPickingLink, self).setUp()
        self.picking = self.env["stock.picking"].search([], limit=1)

    def test_calendar_picking_link(self):
        calendar_picking_link_action = self.picking.action_show_events()
        event = (
            self.env["calendar.event"]
            .with_context(**calendar_picking_link_action["context"])
            .create(
                {
                    "name": "picking",
                    "start": "2019-10-29 10:00:00",
                    "stop": "2019-10-29 11:00:00",
                }
            )
        )
        self.assertEqual(self.picking.event_count, 1)
        self.assertEqual(
            self.env["calendar.event"].search(calendar_picking_link_action["domain"]),
            event,
        )
