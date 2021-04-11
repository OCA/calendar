from odoo.addons.calendar.tests import (
    test_calendar_recurrent_event_case2 as calendar_tests,
)


class TestCalendarV14(calendar_tests.TestRecurrentEvent):
    # disable test functions testing specifics of v13
    def test_recurrent_meeting4(self):
        pass

    def test_recurrent_meeting5(self):
        pass

    def test_recurrent_meeting6(self):
        pass
