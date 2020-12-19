# Copyright 2020 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_test_helper import FakeModelLoader

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import SavepointCase

CALENDAR = [
    ("2020-04-06 08:00:00", "2020-04-06 12:00:00"),
    ("2020-04-06 14:00:00", "2020-04-06 18:00:00"),
    ("2020-04-07 08:00:00", "2020-04-07 12:00:00"),
    ("2020-04-07 14:00:00", "2020-04-07 18:00:00"),
]

# le get_bookable_slot est appeler sur quel object
# warehouse, personne (coiffeur), matériel (ressource)
# plusieurs chose en même temps? (intersection de calendrier ou // de calendrier)

to_string = fields.Datetime.to_string


class TestBooking(SavepointCase, FakeModelLoader):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import ResPartner

        cls.loader.update_registry((ResPartner,))

        cls.partner = cls.env["res.partner"].search([], limit=1)
        cls.partner.slot_capacity = 1
        cls.partner.slot_duration = 90
        for event in CALENDAR:
            cls.env["calendar.event"].create(
                {
                    "name": "Foo",
                    "start": event[0],
                    "stop": event[1],
                    "booking_type": "bookable",
                    "res_model_id": cls.env.ref("base.model_res_partner").id,
                    "res_id": cls.partner.id,
                }
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.loader.restore_registry()

    def _convert_to_string(self, slots):
        for slot in slots:
            for key in ["start", "stop"]:
                slot[key] = to_string(slot[key])
        return slots

    def _get_slot(self, start, stop):
        return self._convert_to_string(self.partner.get_bookable_slot(start, stop))

    def _book_slot(self, start, stop):
        return self.partner.book_slot(
            {
                "start": start,
                "stop": stop,
                "name": "foo",
            }
        )

    def test_get_bookable_slot_case_1(self):
        slots = self._get_slot("2020-04-06 08:00:00", "2020-04-06 18:00:00")
        expected = [
            {"start": "2020-04-06 08:00:00", "stop": "2020-04-06 09:30:00"},
            {"start": "2020-04-06 09:30:00", "stop": "2020-04-06 11:00:00"},
            {"start": "2020-04-06 14:00:00", "stop": "2020-04-06 15:30:00"},
            {"start": "2020-04-06 15:30:00", "stop": "2020-04-06 17:00:00"},
        ]
        self.assertEqual(slots, expected)

    def test_get_bookable_slot_case_2(self):
        slots = self._get_slot("2020-04-06 09:00:00", "2020-04-06 17:00:00")
        expected = [
            {"start": "2020-04-06 09:00:00", "stop": "2020-04-06 10:30:00"},
            {"start": "2020-04-06 10:30:00", "stop": "2020-04-06 12:00:00"},
            {"start": "2020-04-06 14:00:00", "stop": "2020-04-06 15:30:00"},
            {"start": "2020-04-06 15:30:00", "stop": "2020-04-06 17:00:00"},
        ]
        self.assertEqual(slots, expected)

    def test_get_bookable_slot_case_3(self):
        slots = self._get_slot("2020-04-06 09:00:00", "2020-04-06 15:00:00")
        expected = [
            {"start": "2020-04-06 09:00:00", "stop": "2020-04-06 10:30:00"},
            {"start": "2020-04-06 10:30:00", "stop": "2020-04-06 12:00:00"},
        ]
        self.assertEqual(slots, expected)

    def test_get_bookable_slot_case_4(self):
        slots = self._get_slot("2020-04-06 11:00:00", "2020-04-06 18:00:00")
        expected = [
            {"start": "2020-04-06 14:00:00", "stop": "2020-04-06 15:30:00"},
            {"start": "2020-04-06 15:30:00", "stop": "2020-04-06 17:00:00"},
        ]
        self.assertEqual(slots, expected)

    def test_get_bookable_slot_case_5(self):
        slots = self._get_slot("2020-04-06 11:00:00", "2020-04-06 15:00:00")
        expected = []
        self.assertEqual(slots, expected)

    def test_get_bookable_slot_case_6(self):
        self._book_slot("2020-04-06 09:30:00", "2020-04-06 11:00:00")
        slots = self._get_slot("2020-04-06 08:00:00", "2020-04-06 18:00:00")
        expected = [
            {"start": "2020-04-06 08:00:00", "stop": "2020-04-06 09:30:00"},
            {"start": "2020-04-06 14:00:00", "stop": "2020-04-06 15:30:00"},
            {"start": "2020-04-06 15:30:00", "stop": "2020-04-06 17:00:00"},
        ]
        self.assertEqual(slots, expected)

    def test_get_bookable_slot_case_7(self):
        self._book_slot("2020-04-06 09:00:00", "2020-04-06 10:30:00")
        slots = self._get_slot("2020-04-06 08:00:00", "2020-04-06 18:00:00")
        expected = [
            {"start": "2020-04-06 10:30:00", "stop": "2020-04-06 12:00:00"},
            {"start": "2020-04-06 14:00:00", "stop": "2020-04-06 15:30:00"},
            {"start": "2020-04-06 15:30:00", "stop": "2020-04-06 17:00:00"},
        ]
        self.assertEqual(slots, expected)

    def test_book(self):
        slot = self._book_slot("2020-04-06 08:00:00", "2020-04-06 09:30:00")
        self.assertEqual(to_string(slot["start"]), "2020-04-06 08:00:00")
        self.assertEqual(to_string(slot["stop"]), "2020-04-06 09:30:00")

    def test_book_full(self):
        self._book_slot("2020-04-06 08:00:00", "2020-04-06 09:30:00")
        with self.assertRaises(UserError) as err:
            self._book_slot("2020-04-06 08:00:00", "2020-04-06 09:30:00")
        self.assertEqual("The slot is not available anymore", err.exception.name)

    def test_book_on_close_slot(self):
        with self.assertRaises(UserError) as err:
            self._book_slot("2020-04-06 07:00:00", "2020-04-06 08:30:00")
        self.assertEqual("The slot is not on a bookable zone", err.exception.name)

    def test_book_invalid_slot_duration(self):
        with self.assertRaises(UserError) as err:
            self._book_slot("2020-04-06 08:00:00", "2020-04-06 08:30:00")
        self.assertEqual("The slot duration is not valid", err.exception.name)
