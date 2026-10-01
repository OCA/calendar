# Copyright (C) 2024 - ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from datetime import datetime

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.misc import file_path


@tagged("-at_install", "post_install")
class TestImportIcs(TransactionCase):
    def setUp(self):
        super().setUp()
        self.user = self.env.ref("base.user_admin")
        self.user.group_ids = [
            Command.link(self.env.ref("calendar_import_ics.group_calendar_import").id)
        ]
        self.partner = self.env["res.partner"].create({"name": "ICS test calendar"})
        self.event_model = self.env["calendar.event"].with_user(self.user)
        self.import_wiz = self.env["calendar.import.ics"].with_user(self.user)

    @classmethod
    def _get_test_file(cls, file_name):
        path = file_path(f"calendar_import_ics/tests/sample_files/{file_name}")
        with open(path, "rb") as file:
            return base64.encodebytes(file.read())

    def _import_content(self, content, **values):
        wizard = self.import_wiz.create(
            {
                "import_ics_file": base64.b64encode(content.encode()),
                "import_ics_filename": "events.ics",
                "do_remove_old_event": False,
                "partner_id": self.partner.id,
                **values,
            }
        )
        wizard.button_import()
        return wizard

    def test_default_partner(self):
        wizard = self._import_content(
            "BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR", partner_id=False
        )
        self.assertEqual(wizard.partner_id, self.user.partner_id)

    def test_import_ics(self):
        events_before_imp = self.event_model.search([])
        filename = "test_calendar.ics"
        wiz = self.import_wiz.create(
            {
                "import_ics_file": self._get_test_file(filename),
                "import_ics_filename": filename,
                "partner_id": self.partner.id,
            }
        )
        wiz.button_import()
        self.assertEqual(wiz.partner_id.id, self.partner.id)
        events_after_imp = self.event_model.search([])
        self.assertEqual(len(events_after_imp) - len(events_before_imp), 4)
        uid = "ed27f2b89f945c7692547a2903c20cbe80de6cc6"
        start_date = datetime(2006, 10, 10, 20, 00, 00)
        end_date = datetime(2006, 10, 10, 21, 00, 00)
        name = "Event 1 Test"
        event_1 = self.event_model.search([("event_identifier", "=", uid)])
        self.assertEqual(event_1.event_identifier, uid)
        self.assertEqual(event_1.start, start_date)
        self.assertEqual(event_1.stop, end_date)
        self.assertEqual(event_1.name, name)
        self.assertEqual(event_1.partner_ids.ids, [self.partner.id])
        filename = "test_calendar_2.ics"
        wiz = self.import_wiz.create(
            {
                "import_ics_file": self._get_test_file(filename),
                "import_ics_filename": filename,
                "partner_id": self.partner.id,
            }
        )
        wiz.button_import()
        event_1 = self.event_model.search([("event_identifier", "=", uid)])
        start_date = datetime(2006, 10, 10, 21, 00, 00)
        end_date = datetime(2006, 10, 10, 22, 00, 00)
        name = "Event 1 Test Renamed"
        self.assertEqual(event_1.event_identifier, uid)
        self.assertEqual(event_1.start, start_date)
        self.assertEqual(event_1.stop, end_date)
        self.assertEqual(event_1.name, name)
        self.assertEqual(event_1.partner_ids.ids, [self.partner.id])
        filename = "test_calendar_3.ics"
        wiz = self.import_wiz.create(
            {
                "import_ics_file": self._get_test_file(filename),
                "import_ics_filename": filename,
                "import_start_date": datetime(2004, 10, 10),
                "import_end_date": datetime(2044, 10, 10),
                "partner_id": self.partner.id,
            }
        )
        wiz.button_import()
        event_1 = self.event_model.search([("event_identifier", "=", uid)])
        self.assertFalse(event_1)
        wiz = self.import_wiz.create(
            {
                "import_ics_file": self._get_test_file(filename),
                "import_ics_filename": "random_name.xslx",
            }
        )
        with self.assertRaises(ValidationError):
            wiz.button_import()

    def test_all_day_and_timezone_aware_events(self):
        content = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:all-day@example.com
SUMMARY:All-day event
DTSTART;VALUE=DATE:20240901
DTEND;VALUE=DATE:20240903
END:VEVENT
BEGIN:VEVENT
UID:timed@example.com
SUMMARY:Denver event
DTSTART;TZID=America/Denver:20240901T100000
DTEND;TZID=America/Denver:20240901T110000
END:VEVENT
END:VCALENDAR"""
        self._import_content(content)
        all_day = self.event_model.search(
            [("event_identifier", "=", "all-day@example.com")]
        )
        timed = self.event_model.search(
            [("event_identifier", "=", "timed@example.com")]
        )
        self.assertTrue(all_day.allday)
        self.assertEqual(all_day.start_date.isoformat(), "2024-09-01")
        self.assertEqual(all_day.stop_date.isoformat(), "2024-09-02")
        self.assertEqual(timed.start, datetime(2024, 9, 1, 16))
        self.assertEqual(timed.stop, datetime(2024, 9, 1, 17))
        self._import_content(content)
        self.assertEqual(
            self.event_model.search_count(
                [
                    (
                        "event_identifier",
                        "in",
                        ["all-day@example.com", "timed@example.com"],
                    )
                ]
            ),
            2,
        )

    def test_description_import_and_update(self):
        content = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:description@example.com
SUMMARY:Described event
DESCRIPTION:First line\\nSecond <script>alert(1)</script>
DTSTART:20261015T120000Z
DTEND:20261015T130000Z
END:VEVENT
END:VCALENDAR"""
        self._import_content(content)
        event = self.event_model.search(
            [("event_identifier", "=", "description@example.com")]
        )
        self.assertIn("First line", event.description)
        self.assertIn("Second &lt;script&gt;alert(1)&lt;/script&gt;", event.description)
        self.assertNotIn("<script>", event.description)

        rich_content = content.replace(
            "DESCRIPTION:First line\\nSecond <script>alert(1)</script>",
            "DESCRIPTION:Updated plain\n"
            "X-ALT-DESC;FMTTYPE=text/html:<div>Updated <i>rich</i> <b>text</b>"
            '<script>alert(1)</script><img src="" id="x_image_0"></div>',
        )
        self._import_content(rich_content)
        self.assertIn("<i>rich</i>", event.description)
        self.assertIn("<b>text</b>", event.description)
        self.assertNotIn("First line", event.description)
        self.assertNotIn("Updated plain", event.description)
        self.assertNotIn("<script>", event.description)
        self.assertNotIn("<img", event.description)
        self.assertEqual(
            self.event_model.search_count(
                [("event_identifier", "=", "description@example.com")]
            ),
            1,
        )

    def test_recurring_event_import_is_idempotent(self):
        content = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:daily@example.com
SUMMARY:Daily event
DTSTART:20240901T100000Z
DTEND:20240901T110000Z
RRULE:FREQ=DAILY;COUNT=3
END:VEVENT
END:VCALENDAR"""
        self._import_content(content)
        event = self.event_model.search(
            [("event_identifier", "=", "daily@example.com")]
        )
        self.assertTrue(event.recurrence_id)
        self.assertEqual(len(event.recurrence_id.calendar_event_ids), 3)
        with self.assertRaises(ValidationError):
            self._import_content(content, import_start_date="2024-09-02")
        self._import_content(
            content.replace("COUNT=3", "COUNT=2").replace(
                "Daily event", "Updated daily event"
            )
        )
        event = self.event_model.search(
            [("event_identifier", "=", "daily@example.com")]
        )
        self.assertEqual(event.name, "Updated daily event")
        self.assertEqual(len(event.recurrence_id.calendar_event_ids), 2)
        self._import_content(content)
        self.assertEqual(
            self.event_model.search_count(
                [("event_identifier", "=", "daily@example.com")]
            ),
            1,
        )
        self.assertEqual(len(event.recurrence_id.calendar_event_ids), 3)

    def test_malformed_file_does_not_import_events(self):
        for content in (
            "not an ICS file",
            """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Missing UID
DTSTART:20240901T100000Z
DTEND:20240901T110000Z
END:VEVENT
END:VCALENDAR""",
            """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:invalid-rule@example.com
SUMMARY:Invalid recurrence
DTSTART:20240901T100000Z
DTEND:20240901T110000Z
RRULE:FREQ=INVALID
END:VEVENT
END:VCALENDAR""",
        ):
            with self.subTest(content=content), self.assertRaises(ValidationError):
                self._import_content(content)

    def test_cleanup_keeps_events_shared_with_another_partner(self):
        content = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:shared@example.com
SUMMARY:Shared event
DTSTART:20240901T100000Z
DTEND:20240901T110000Z
END:VEVENT
END:VCALENDAR"""
        self._import_content(content)
        event = self.event_model.search(
            [("event_identifier", "=", "shared@example.com")]
        )
        other_partner = self.env["res.partner"].create({"name": "Other partner"})
        event.write({"partner_ids": [Command.link(other_partner.id)]})
        self._import_content(
            "BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR",
            do_remove_old_event=True,
        )
        self.assertTrue(event.exists())
        self.assertEqual(event.partner_ids, other_partner)

    def test_import_wizard_requires_group(self):
        self.user.group_ids = [
            Command.unlink(self.env.ref("calendar_import_ics.group_calendar_import").id)
        ]
        with self.assertRaises(AccessError):
            self.import_wiz.create(
                {
                    "import_ics_file": base64.b64encode(b"test"),
                    "import_ics_filename": "test.ics",
                }
            )
