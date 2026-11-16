# Copyright (C) 2024 - ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from datetime import date, datetime
from unittest.mock import patch

import vobject
from freezegun import freeze_time

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("-at_install", "post_install")
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

    @freeze_time("2024-05-21")
    def test_export_group_access(self):
        admin = self.env.ref("base.user_admin")
        wizard = self.export_wiz.with_user(admin)
        with self.assertRaises(AccessError):
            wizard.create({"partner_id": admin.partner_id.id})

        admin.write(
            {
                "group_ids": [
                    Command.link(
                        self.env.ref("calendar_export_ics.group_calendar_export").id
                    )
                ]
            }
        )
        export = wizard.create({"partner_id": admin.partner_id.id})
        self.assertEqual(export.button_export()["res_id"], export.id)

    @freeze_time("2024-05-21")
    def test_empty_and_single_event_exports(self):
        for end_date, expected in [
            (date(2024, 5, 23), []),
            (date(2024, 5, 24), ["Event 5"]),
        ]:
            with self.subTest(end_date=end_date):
                wiz = self.export_wiz.create(
                    {"partner_id": self.partner_2.id, "export_end_date": end_date}
                )
                action = wiz.button_export()
                calendar = vobject.readOne(
                    base64.b64decode(wiz.export_ics_file).decode("utf-8")
                )
                self.assertEqual(
                    [
                        event.summary.value
                        for event in calendar.contents.get("vevent", [])
                    ],
                    expected,
                )
                self.assertEqual(action["res_id"], wiz.id)
                self.assertTrue(wiz.export_ics_filename.endswith(".ics"))

    @freeze_time("2024-05-21")
    def test_all_day_event_export(self):
        self.event_model.create(
            {
                "name": "All Day Event",
                "start": datetime(2024, 5, 25),
                "stop": datetime(2024, 5, 26),
                "allday": True,
                "partner_ids": [(4, self.partner_1.id)],
            }
        )
        wiz = self.export_wiz.create(
            {"partner_id": self.partner_1.id, "export_end_date": date(2024, 5, 25)}
        )
        calendar = vobject.readOne(
            base64.b64decode(wiz.generate_ics_content()).decode("utf-8")
        )
        all_day = next(
            event
            for event in calendar.vevent_list
            if event.summary.value == "All Day Event"
        )
        self.assertNotIsInstance(all_day.dtstart.value, datetime)
        self.assertNotIsInstance(all_day.dtend.value, datetime)
        self.assertEqual(all_day.dtstart.value, date(2024, 5, 25))
        self.assertEqual(all_day.dtend.value, date(2024, 5, 27))

    @freeze_time("2024-05-21")
    def test_all_day_export_with_timed_source(self):
        event = self.event_model.create(
            {
                "name": "All Day Event",
                "start": datetime(2024, 5, 25),
                "stop": datetime(2024, 5, 26),
                "allday": True,
                "partner_ids": [Command.link(self.partner_1.id)],
            }
        )
        source = (
            b"BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\n"
            b"UID:all-day@example.com\nSUMMARY:All Day Event\n"
            b"DTSTART;TZID=America/New_York:20240525T000000\n"
            b"DTEND;TZID=America/New_York:20240526T000000\n"
            b"END:VEVENT\nEND:VCALENDAR"
        )
        wizard = self.export_wiz.create(
            {"partner_id": self.partner_1.id, "export_end_date": date(2024, 5, 25)}
        )
        with patch.object(
            type(self.event_model), "_get_ics_file", return_value={event.id: source}
        ):
            calendar = vobject.readOne(
                base64.b64decode(wizard.generate_ics_content()).decode("utf-8")
            )
        self.assertEqual(calendar.vevent.dtstart.value, date(2024, 5, 25))
        self.assertEqual(calendar.vevent.dtend.value, date(2024, 5, 27))

    @freeze_time("2024-05-21")
    def test_recurring_event_export(self):
        self.event_model.create(
            {
                "name": "Recurring Event",
                "start": datetime(2024, 5, 25, 12),
                "stop": datetime(2024, 5, 25, 13),
                "rrule": "FREQ=DAILY;INTERVAL=1;COUNT=2",
                "recurrency": True,
                "partner_ids": [(4, self.partner_1.id)],
            }
        )
        wiz = self.export_wiz.create({"partner_id": self.partner_1.id})
        calendar = vobject.readOne(
            base64.b64decode(wiz.generate_ics_content()).decode("utf-8")
        )
        recurring = [
            event
            for event in calendar.vevent_list
            if event.summary.value == "Recurring Event"
        ]
        self.assertTrue(recurring)
        self.assertEqual(len(recurring), 1)
        self.assertTrue(any(event.rrule.value for event in recurring))

        wiz.export_end_date = date(2024, 5, 26)
        calendar = vobject.readOne(
            base64.b64decode(wiz.generate_ics_content()).decode("utf-8")
        )
        recurring = [
            event
            for event in calendar.vevent_list
            if event.summary.value == "Recurring Event"
        ]
        self.assertEqual(len(recurring), 2)
        self.assertTrue(all("rrule" not in event.contents for event in recurring))

    @freeze_time("2024-05-21")
    def test_timezone_aware_event_export(self):
        self.event_model.create(
            {
                "name": "Timezone Event",
                "start": datetime(2024, 5, 25, 20),
                "stop": datetime(2024, 5, 25, 21),
                "event_tz": "America/New_York",
                "partner_ids": [(4, self.partner_1.id)],
            }
        )
        wiz = self.export_wiz.create(
            {"partner_id": self.partner_1.id, "export_end_date": date(2024, 5, 25)}
        )
        calendar = vobject.readOne(
            base64.b64decode(wiz.generate_ics_content()).decode("utf-8")
        )
        event = next(
            event
            for event in calendar.vevent_list
            if event.summary.value == "Timezone Event"
        )
        self.assertEqual(event.dtstart.value.utcoffset().total_seconds(), 0)
        self.assertEqual(event.dtstart.value.hour, 20)
