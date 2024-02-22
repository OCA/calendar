# Copyright (C) 2024 - ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource
from odoo.tests.common import TransactionCase


class TestImportIcs(TransactionCase):
    def setUp(self):
        super(TestImportIcs, self).setUp()
        self.event_model = self.env["calendar.event"]
        self.import_wiz = self.env["calendar.import.ics"]

    @classmethod
    def _get_test_file(cls, file_name):
        file_path = get_module_resource(
            "calendar_import_ics", "tests/sample_files", file_name
        )
        with open(file_path, "rb") as file:
            return base64.encodebytes(file.read())

    def test_import_ics(self):
        events_before_imp = self.event_model.search([])
        filename = "test_calendar.ics"
        wiz = self.import_wiz.create(
            {
                "import_ics_file": self._get_test_file(filename),
                "import_ics_filename": filename,
            }
        )
        wiz.button_import()
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
        filename = "test_calendar_2.ics"
        wiz = self.import_wiz.create(
            {
                "import_ics_file": self._get_test_file(filename),
                "import_ics_filename": filename,
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
        filename = "test_calendar_3.ics"
        wiz = self.import_wiz.create(
            {
                "import_ics_file": self._get_test_file(filename),
                "import_ics_filename": filename,
                "import_start_date": datetime(2004, 10, 10),
                "import_end_date": datetime(2044, 10, 10),
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
