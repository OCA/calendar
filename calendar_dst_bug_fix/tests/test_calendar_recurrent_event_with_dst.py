
# -*- coding: utf-8 -*-

from odoo.tests import common
from datetime import datetime
import pytz


class TestRecurrentEventWithDst(common.TransactionCase):

    def setUp(self):
        super(TestRecurrentEventWithDst, self).setUp()
        self.calendar_event = self.env['calendar.event']

    def test_recurrent_meeting_calendar_event_read_dst_starts(self):
        # March 10 2019 at 2 am the los angeles daylight saving time starts
        timezone = pytz.timezone("America/Los_Angeles")
        start = datetime(2019, 3, 9, 10, 30)
        end = datetime(2019, 3, 9, 11, 30)
        self.calendar_event.create({
            'count': 2,
            'start': timezone.localize(start),
            'stop': timezone.localize(end),
            'duration': 1.0,
            'name': 'OCA Meeting',
            'recurrency': True,
            'rrule_type': 'daily'
        })
        context = {"tz": "America/Los_Angeles"}
        recurrent_meetings = self.calendar_event.with_context(context).search(
            [('start', '>=', '2019-03-09'), ('stop', '<=', '2019-03-10')])
        self.assertEqual(recurrent_meetings[1].read(
            ['start'])[0]['start'], '2019-03-09 10:30:00',
            'Recurrent daily meeting are not handling DST \
             change correctly on CalendarEvent.read')
        self.assertEqual(recurrent_meetings[0].read(
            ['start'])[0]['start'], '2019-03-10 09:30:00',
            'Recurrent daily meeting are not handling DST \
             change correctly on CalendarEvent.read')

    def test_recurrent_meeting_calendar_event_read_dst_ends(self):
        # November 3 2019 at 2 am the los angeles daylight saving time ends
        timezone = pytz.timezone("America/Los_Angeles")
        start = datetime(2019, 11, 2, 10, 30)
        end = datetime(2019, 11, 2, 11, 30)
        self.calendar_event.create({
            'count': 2,
            'start': timezone.localize(start),
            'stop': timezone.localize(end),
            'duration': 1.0,
            'name': 'OCA Meeting 2',
            'recurrency': True,
            'rrule_type': 'daily'
        })
        context = {"tz": "America/Los_Angeles"}
        recurrent_meetings = self.calendar_event.with_context(context).search(
            [('start', '>=', '2019-11-02'), ('stop', '<=', '2019-11-03')])
        self.assertEqual(recurrent_meetings[1].read(
            ['start'])[0]['start'], '2019-11-02 10:30:00',
            'Recurrent daily meeting are not handling DST \
             change correctly on CalendarEvent.read')
        self.assertEqual(recurrent_meetings[0].read(
            ['start'])[0]['start'], '2019-11-03 11:30:00',
            'Recurrent daily meeting are not handling DST \
             change correctly on CalendarEvent.read')
