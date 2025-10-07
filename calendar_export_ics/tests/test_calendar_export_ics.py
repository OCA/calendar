# Copyright (C) 2024 - ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from datetime import date, datetime

from freezegun import freeze_time

from odoo.tests.common import TransactionCase


class TestExportIcs(TransactionCase):
    def setUp(self):
        super().setUp()
        self.event_model = self.env["calendar.event"]
        self.partner_model = self.env["res.partner"]
        self.export_wiz = self.env["calendar.export.ics"]

        self.partner_1 = self.partner_model.create({"name": "Partner 1"})
        self.partner_2 = self.partner_model.create({"name": "Partner 2"})
        self.event_1 = self.event_model.create(
            {
                "name": "Event 1",
                "start": datetime(2024, 5, 22, 20, 00, 00),
                "stop": datetime(2024, 5, 22, 21, 00, 00),
                "partner_ids": [(4, self.partner_1.id)],
            }
        )
        self.event_2 = self.event_model.create(
            {
                "name": "Event 2",
                "start": datetime(2024, 5, 22, 18, 00, 00),
                "stop": datetime(2024, 5, 22, 18, 30, 00),
                "partner_ids": [(4, self.partner_1.id)],
            }
        )
        self.event_3 = self.event_model.create(
            {
                "name": "Event 3",
                "start": datetime(2024, 5, 19, 21, 00, 00),
                "stop": datetime(2024, 5, 19, 22, 00, 00),
                "partner_ids": [(4, self.partner_1.id)],
            }
        )
        self.event_4 = self.event_model.create(
            {
                "name": "Event 4",
                "start": datetime(2024, 5, 23, 15, 00, 00),
                "stop": datetime(2024, 5, 23, 17, 00, 00),
                "partner_ids": [(4, self.partner_1.id)],
            }
        )
        self.event_5 = self.event_model.create(
            {
                "name": "Event 5",
                "start": datetime(2024, 5, 24, 15, 00, 00),
                "stop": datetime(2024, 5, 24, 17, 00, 00),
                "partner_ids": [(4, self.partner_2.id)],
            }
        )
        self.event_6 = self.event_model.create(
            {
                "name": "Event 6",
                "start": datetime(2024, 6, 24, 15, 00, 00),
                "stop": datetime(2024, 6, 24, 17, 00, 00),
                "partner_ids": [(4, self.partner_1.id)],
            }
        )

    @freeze_time("2024-05-21")
    def test_export_ics(self):
        wiz = self.export_wiz.create(
            {"partner_id": self.partner_1.id, "export_end_date": date(2024, 6, 1)}
        )
        wiz.button_export()
        file_content = wiz.export_ics_file
        decoded_content = base64.b64decode(file_content)
        ics_content = decoded_content.decode()
        # Check that events 1,2,4 are exported
        self.assertIn("\nSUMMARY:Event 1", ics_content)
        self.assertIn("\nSUMMARY:Event 2", ics_content)
        self.assertIn("\nSUMMARY:Event 4", ics_content)
        self.assertNotIn("SUMMARY:Event 3", ics_content)
        self.assertNotIn("SUMMARY:Event 5", ics_content)
        self.assertNotIn("SUMMARY:Event 6", ics_content)
