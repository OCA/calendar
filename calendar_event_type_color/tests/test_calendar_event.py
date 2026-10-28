from odoo.tests.common import TransactionCase


class TestCalendarEventColor(TransactionCase):
    def test_color_computation_with_tag(self):
        tag = self.env["calendar.event.type"].create(
            {
                "name": "Blue",
                "color": 5,
            }
        )
        event = self.env["calendar.event"].create(
            {
                "name": "Event with Tag",
                "categ_ids": [(6, 0, [tag.id])],
            }
        )
        event._compute_color()
        self.assertEqual(event.color, 5)

    def test_color_computation_without_tag(self):
        event = self.env["calendar.event"].create(
            {
                "name": "Event without Tag",
            }
        )
        event._compute_color()
        self.assertEqual(event.color, 0)
