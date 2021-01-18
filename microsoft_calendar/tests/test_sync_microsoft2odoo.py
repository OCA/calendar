# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date, datetime

import pytz
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo.tests.common import SavepointCase

from odoo.addons.microsoft_calendar.utils.microsoft_calendar import MicrosoftEvent


class TestSyncMicrosoft2Odoo(SavepointCase):
    @property
    @freeze_time('2020-06-03')
    def now(self):
        return pytz.utc.localize(datetime.now()).isoformat()

    def setUp(self):
        super().setUp()
        self.recurrence_id = "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA"
        values = [
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAACyq4xQ=="',
                "createdDateTime": "2020-05-06T07:03:49.1444085Z",
                "lastModifiedDateTime": "2020-05-06T07:00:00Z",
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAACyq4xQ==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E00800000000874F057E7423D601000D848B1B7F8C",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": None,
                "showAs": "busy",
                "type": "seriesMaster",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFAAALLLTEAAAA&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:00:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "recurrence": {
                    "pattern": {
                        "type": "daily",
                        "interval": 1,
                        "month": 0,
                        "dayOfMonth": 0,
                        "firstDayOfWeek": "sunday",
                        "index": "first",
                    },
                    "range": {
                        "type": "endDate",
                        "startDate": "2020-05-03",
                        "endDate": "2020-05-05",
                        "recurrenceTimeZone": "Romance Standard Time",
                        "numberOfOccurrences": 0,
                    },
                },
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAALKrjF"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX7vTsS0AARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:00:00.0000000", "timeZone": "UTC"},
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAALKrjF"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX774WtQAAAEYAAAJAcu19N72jSr9Rp1mE2xWABwBlLa4RUBXJToExnebpwea2AAACAQ0AAABlLa4RUBXJToExnebpwea2AAAACyy0xAAAABA=",
                "start": {"dateTime": "2020-05-04T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-04T16:00:00.0000000", "timeZone": "UTC"},
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAALKrjF"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX8IdBHsAARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-05T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-05T16:00:00.0000000", "timeZone": "UTC"},
            },
        ]

        self.env["calendar.event"]._sync_microsoft2odoo(MicrosoftEvent(values))

        self.datetime_future = pytz.utc.localize(
            datetime.now() + relativedelta(days=1)
        ).isoformat()

    @freeze_time('2020-06-03')
    def sync(self, events):

        self.env["calendar.event"]._sync_microsoft2odoo(events)

    @freeze_time('2020-06-03')
    def test_new_microsoft_recurrence(self):

        recurrence = self.env["calendar.recurrence"].search(
            [("microsoft_id", "=", self.recurrence_id)]
        )
        events = recurrence.calendar_event_ids
        self.assertTrue(recurrence, "It should have created an recurrence")
        self.assertEqual(len(events), 3, "It should have created 3 events")
        self.assertEqual(recurrence.base_event_id, events[0])
        self.assertEqual(
            events.mapped("name"),
            ["My recurrent event", "My recurrent event", "My recurrent event"],
        )
        self.assertFalse(events[0].allday)
        self.assertEqual(events[0].start, datetime(2020, 5, 3, 14, 30))
        self.assertEqual(events[0].stop, datetime(2020, 5, 3, 16, 00))
        self.assertEqual(events[1].start, datetime(2020, 5, 4, 14, 30))
        self.assertEqual(events[1].stop, datetime(2020, 5, 4, 16, 00))
        self.assertEqual(events[2].start, datetime(2020, 5, 5, 14, 30))
        self.assertEqual(events[2].stop, datetime(2020, 5, 5, 16, 00))

    @freeze_time('2020-06-03')
    def test_microsoft_recurrence_delete_one_event(self):
        values = [
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAADIaZKQ=="',
                "createdDateTime": "2020-05-06T07:03:49.1444085Z",
                "lastModifiedDateTime": self.datetime_future,
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAADIaZKQ==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E00800000000874F057E7423D601000000000000000010000000C6918C4B44D2D84586351FEC8B1B7F8C",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": None,
                "showAs": "busy",
                "type": "seriesMaster",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:00:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "recurrence": {
                    "pattern": {
                        "type": "daily",
                        "interval": 1,
                        "month": 0,
                        "dayOfMonth": 0,
                        "firstDayOfWeek": "sunday",
                        "index": "first",
                    },
                    "range": {
                        "type": "endDate",
                        "startDate": "2020-05-03",
                        "endDate": "2020-05-05",
                        "recurrenceTimeZone": "Romance Standard Time",
                        "numberOfOccurrences": 0,
                    },
                },
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMhpkp"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX7vTsS0AARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:00:00.0000000", "timeZone": "UTC"},
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMhpkp"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX8IdBHsAARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-05T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-05T16:00:00.0000000", "timeZone": "UTC"},
            },
        ]

        self.env["calendar.event"]._sync_microsoft2odoo(MicrosoftEvent(values))

        recurrence = self.env["calendar.recurrence"].search(
            [("microsoft_id", "=", self.recurrence_id)]
        )
        events = self.env["calendar.event"].search(
            [("recurrence_id", "=", recurrence.id)], order="start asc"
        )
        self.assertTrue(recurrence, "It should keep the recurrence")
        self.assertEqual(len(events), 2, "It should keep 2 events")
        self.assertEqual(recurrence.base_event_id, events[0])
        self.assertEqual(
            events.mapped("name"), ["My recurrent event", "My recurrent event"]
        )

    @freeze_time('2020-06-03')
    def test_microsoft_recurrence_change_name_one_event(self):
        values = [
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAADIaZKQ=="',
                "createdDateTime": "2020-05-06T07:03:49.1444085Z",
                "lastModifiedDateTime": self.datetime_future,
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAADIaZKQ==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E00800000000874F057E7423D601000000000000000010000000C6918C4B44D2D84586351FEC8B1B7F8C",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": None,
                "showAs": "busy",
                "type": "seriesMaster",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:00:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "recurrence": {
                    "pattern": {
                        "type": "daily",
                        "interval": 1,
                        "month": 0,
                        "dayOfMonth": 0,
                        "firstDayOfWeek": "sunday",
                        "index": "first",
                    },
                    "range": {
                        "type": "endDate",
                        "startDate": "2020-05-03",
                        "endDate": "2020-05-05",
                        "recurrenceTimeZone": "Romance Standard Time",
                        "numberOfOccurrences": 0,
                    },
                },
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMhpkp"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX7vTsS0AARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:00:00.0000000", "timeZone": "UTC"},
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAADIaZKQ=="',
                "createdDateTime": "2020-05-06T08:01:32.4884797Z",
                "lastModifiedDateTime": self.datetime_future,
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAADIaZKQ==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E00807E40504874F057E7423D601000000000000000010000000C6918C4B44D2D84586351FEC8B1B7F8C",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event 2",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "originalStart": "2020-05-04T14:30:00Z",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "showAs": "busy",
                "type": "exception",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX774WtQAAAEYAAAJAcu19N72jSr9Rp1mE2xWABwBlLa4RUBXJToExnebpwea2AAACAQ0AAABlLa4RUBXJToExnebpwea2AAAACyy0xAAAABA%3D&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX774WtQAAAEYAAAJAcu19N72jSr9Rp1mE2xWABwBlLa4RUBXJToExnebpwea2AAACAQ0AAABlLa4RUBXJToExnebpwea2AAAACyy0xAAAABA=",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-04T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-04T16:00:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMhpkp"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX8IdBHsAARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-05T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-05T16:00:00.0000000", "timeZone": "UTC"},
            },
        ]

        self.env["calendar.event"]._sync_microsoft2odoo(MicrosoftEvent(values))

        recurrence = self.env["calendar.recurrence"].search(
            [("microsoft_id", "=", self.recurrence_id)]
        )
        events = self.env["calendar.event"].search(
            [("recurrence_id", "=", recurrence.id)], order="start asc"
        )
        self.assertTrue(recurrence, "It should have created an recurrence")
        self.assertEqual(len(events), 3, "It should have created 3 events")
        self.assertEqual(recurrence.base_event_id, events[0])
        self.assertEqual(
            events.mapped("name"),
            ["My recurrent event", "My recurrent event 2", "My recurrent event"],
        )

    @freeze_time('2020-06-03')
    def test_microsoft_recurrence_change_name_all_event(self):
        values = [
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAADIaZKQ=="',
                "createdDateTime": "2020-05-06T07:03:49.1444085Z",
                "lastModifiedDateTime": self.datetime_future,
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAADIaZKQ==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E00800000000874F057E7423D601000000000000000010000000C6918C4B44D2D84586351FEC8B1B7F8C",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event 2",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": None,
                "showAs": "busy",
                "type": "seriesMaster",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:00:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "recurrence": {
                    "pattern": {
                        "type": "daily",
                        "interval": 1,
                        "month": 0,
                        "dayOfMonth": 0,
                        "firstDayOfWeek": "sunday",
                        "index": "first",
                    },
                    "range": {
                        "type": "endDate",
                        "startDate": "2020-05-03",
                        "endDate": "2020-05-05",
                        "recurrenceTimeZone": "Romance Standard Time",
                        "numberOfOccurrences": 0,
                    },
                },
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMhpkp"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX7vTsS0AARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:00:00.0000000", "timeZone": "UTC"},
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMhpkp"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX774WtQAAAEYAAAJAcu19N72jSr9Rp1mE2xWABwBlLa4RUBXJToExnebpwea2AAACAQ0AAABlLa4RUBXJToExnebpwea2AAAACyy0xAAAABA=",
                "start": {"dateTime": "2020-05-04T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-04T16:00:00.0000000", "timeZone": "UTC"},
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMhpkp"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX8IdBHsAARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-05T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-05T16:00:00.0000000", "timeZone": "UTC"},
            },
        ]

        self.env["calendar.event"]._sync_microsoft2odoo(MicrosoftEvent(values))

        recurrence = self.env["calendar.recurrence"].search(
            [("microsoft_id", "=", self.recurrence_id)]
        )
        events = self.env["calendar.event"].search(
            [("recurrence_id", "=", recurrence.id)], order="start asc"
        )
        self.assertTrue(recurrence, "It should keep the recurrence")
        self.assertEqual(len(events), 3, "It should keep the 3 events")
        self.assertEqual(recurrence.base_event_id, events[0])
        self.assertEqual(
            events.mapped("name"),
            ["My recurrent event 2", "My recurrent event 2", "My recurrent event 2"],
        )

    @freeze_time('2020-06-03')
    def test_microsoft_recurrence_change_date_one_event(self):
        values = [
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAADIaZPA=="',
                "createdDateTime": "2020-05-06T07:03:49.1444085Z",
                "lastModifiedDateTime": self.datetime_future,
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAADIaZPA==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E00800000000874F057E7423D601000000000000000010000000C6918C4B44D2D84586351FEC8B1B7F8C",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": None,
                "showAs": "busy",
                "type": "seriesMaster",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:00:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "recurrence": {
                    "pattern": {
                        "type": "daily",
                        "interval": 1,
                        "month": 0,
                        "dayOfMonth": 0,
                        "firstDayOfWeek": "sunday",
                        "index": "first",
                    },
                    "range": {
                        "type": "endDate",
                        "startDate": "2020-05-03",
                        "endDate": "2020-05-05",
                        "recurrenceTimeZone": "Romance Standard Time",
                        "numberOfOccurrences": 0,
                    },
                },
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMhpk8"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX7vTsS0AARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:00:00.0000000", "timeZone": "UTC"},
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAADIaZPA=="',
                "createdDateTime": "2020-05-06T08:41:52.1067613Z",
                "lastModifiedDateTime": self.datetime_future,
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAADIaZPA==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E00807E40504874F057E7423D601000000000000000010000000C6918C4B44D2D84586351FEC8B1B7F8C",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "originalStart": "2020-05-04T14:30:00Z",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "showAs": "busy",
                "type": "exception",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX774WtQAAAEYAAAJAcu19N72jSr9Rp1mE2xWABwBlLa4RUBXJToExnebpwea2AAACAQ0AAABlLa4RUBXJToExnebpwea2AAAACyy0xAAAABA%3D&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX774WtQAAAEYAAAJAcu19N72jSr9Rp1mE2xWABwBlLa4RUBXJToExnebpwea2AAACAQ0AAABlLa4RUBXJToExnebpwea2AAAACyy0xAAAABA=",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-04T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-04T17:00:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMhpk8"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX8IdBHsAARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-05T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-05T16:00:00.0000000", "timeZone": "UTC"},
            },
        ]

        self.env["calendar.event"]._sync_microsoft2odoo(MicrosoftEvent(values))

        recurrence = self.env["calendar.recurrence"].search(
            [("microsoft_id", "=", self.recurrence_id)]
        )
        events = self.env["calendar.event"].search(
            [("recurrence_id", "=", recurrence.id)], order="start asc"
        )
        special_event = self.env["calendar.event"].search(
            [
                (
                    "microsoft_id",
                    "=",
                    "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX774WtQAAAEYAAAJAcu19N72jSr9Rp1mE2xWABwBlLa4RUBXJToExnebpwea2AAACAQ0AAABlLa4RUBXJToExnebpwea2AAAACyy0xAAAABA=",
                )
            ]
        )
        self.assertTrue(recurrence, "It should have created an recurrence")
        self.assertTrue(special_event, "It should have created an special event")
        self.assertEqual(len(events), 3, "It should have created 3 events")
        self.assertTrue(special_event in events)
        self.assertEqual(recurrence.base_event_id, events[0])
        self.assertEqual(
            events.mapped("name"),
            ["My recurrent event", "My recurrent event", "My recurrent event"],
        )
        event_not_special = events - special_event
        self.assertEqual(event_not_special[0].start, datetime(2020, 5, 3, 14, 30))
        self.assertEqual(event_not_special[0].stop, datetime(2020, 5, 3, 16, 00))
        self.assertEqual(event_not_special[1].start, datetime(2020, 5, 5, 14, 30))
        self.assertEqual(event_not_special[1].stop, datetime(2020, 5, 5, 16, 00))
        self.assertEqual(special_event.start, datetime(2020, 5, 4, 14, 30))
        self.assertEqual(special_event.stop, datetime(2020, 5, 4, 17, 00))

    @freeze_time('2020-06-03')
    def test_microsoft_recurrence_delete_first_event(self):
        values = [
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAADI/Bnw=="',
                "createdDateTime": "2020-05-06T07:03:49.1444085Z",
                "lastModifiedDateTime": self.datetime_future,
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAADI/Bnw==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E00800000000874F057E7423D601000000000000000010000000C6918C4B44D2D84586351FEC8B1B7F8C",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": None,
                "showAs": "busy",
                "type": "seriesMaster",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:00:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "recurrence": {
                    "pattern": {
                        "type": "daily",
                        "interval": 1,
                        "month": 0,
                        "dayOfMonth": 0,
                        "firstDayOfWeek": "sunday",
                        "index": "first",
                    },
                    "range": {
                        "type": "endDate",
                        "startDate": "2020-05-03",
                        "endDate": "2020-05-05",
                        "recurrenceTimeZone": "Romance Standard Time",
                        "numberOfOccurrences": 0,
                    },
                },
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMj8Gf"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX774WtQAAAEYAAAJAcu19N72jSr9Rp1mE2xWABwBlLa4RUBXJToExnebpwea2AAACAQ0AAABlLa4RUBXJToExnebpwea2AAAACyy0xAAAABA=",
                "start": {"dateTime": "2020-05-04T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-04T16:00:00.0000000", "timeZone": "UTC"},
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMj8Gf"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX8IdBHsAARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-05T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-05T16:00:00.0000000", "timeZone": "UTC"},
            },
        ]

        self.env["calendar.event"]._sync_microsoft2odoo(MicrosoftEvent(values))

        recurrence = self.env["calendar.recurrence"].search(
            [("microsoft_id", "=", self.recurrence_id)]
        )
        events = self.env["calendar.event"].search(
            [("recurrence_id", "=", recurrence.id)], order="start asc"
        )
        self.assertTrue(recurrence, "It should have created an recurrence")
        self.assertEqual(len(events), 2, "It should left 2 events")
        self.assertEqual(recurrence.base_event_id, events[0])
        self.assertEqual(events[0].start, datetime(2020, 5, 4, 14, 30))
        self.assertEqual(events[0].stop, datetime(2020, 5, 4, 16, 00))
        self.assertEqual(events[1].start, datetime(2020, 5, 5, 14, 30))
        self.assertEqual(events[1].stop, datetime(2020, 5, 5, 16, 00))

        # Now we delete lastest event in Outlook.
        values = [
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAADI/Bpg=="',
                "createdDateTime": "2020-05-06T07:03:49.1444085Z",
                "lastModifiedDateTime": self.datetime_future,
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAADI/Bpg==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E00800000000874F057E7423D601000000000000000010000000C6918C4B44D2D84586351FEC8B1B7F8C",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": None,
                "showAs": "busy",
                "type": "seriesMaster",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:00:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "recurrence": {
                    "pattern": {
                        "type": "daily",
                        "interval": 1,
                        "month": 0,
                        "dayOfMonth": 0,
                        "firstDayOfWeek": "sunday",
                        "index": "first",
                    },
                    "range": {
                        "type": "endDate",
                        "startDate": "2020-05-03",
                        "endDate": "2020-05-05",
                        "recurrenceTimeZone": "Romance Standard Time",
                        "numberOfOccurrences": 0,
                    },
                },
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMj8Gm"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX774WtQAAAEYAAAJAcu19N72jSr9Rp1mE2xWABwBlLa4RUBXJToExnebpwea2AAACAQ0AAABlLa4RUBXJToExnebpwea2AAAACyy0xAAAABA=",
                "start": {"dateTime": "2020-05-04T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-04T16:00:00.0000000", "timeZone": "UTC"},
            },
        ]

        self.env["calendar.event"]._sync_microsoft2odoo(MicrosoftEvent(values))

        events = self.env["calendar.event"].search(
            [("recurrence_id", "=", recurrence.id)], order="start asc"
        )
        self.assertEqual(len(events), 1, "It should have created 1 events")
        self.assertEqual(recurrence.base_event_id, events[0])

        # Now, we change end datetime of recurrence in Outlook, so all recurrence is recreated (even deleted events)
        values = [
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAADI/Bqg=="',
                "createdDateTime": "2020-05-06T07:03:49.1444085Z",
                "lastModifiedDateTime": self.datetime_future,
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAADI/Bqg==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E00800000000874F057E7423D601000000000000000010000000C6918C4B44D2D84586351FEC8B1B7F8C",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": None,
                "showAs": "busy",
                "type": "seriesMaster",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:30:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "recurrence": {
                    "pattern": {
                        "type": "daily",
                        "interval": 1,
                        "month": 0,
                        "dayOfMonth": 0,
                        "firstDayOfWeek": "sunday",
                        "index": "first",
                    },
                    "range": {
                        "type": "endDate",
                        "startDate": "2020-05-03",
                        "endDate": "2020-05-05",
                        "recurrenceTimeZone": "Romance Standard Time",
                        "numberOfOccurrences": 0,
                    },
                },
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMj8Gq"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX7vTsS0AARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:30:00.0000000", "timeZone": "UTC"},
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMj8Gq"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX774WtQAAAEYAAAJAcu19N72jSr9Rp1mE2xWABwBlLa4RUBXJToExnebpwea2AAACAQ0AAABlLa4RUBXJToExnebpwea2AAAACyy0xAAAABA=",
                "start": {"dateTime": "2020-05-04T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-04T16:30:00.0000000", "timeZone": "UTC"},
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMj8Gq"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX8IdBHsAARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-05T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-05T16:30:00.0000000", "timeZone": "UTC"},
            },
        ]

        self.env["calendar.event"]._sync_microsoft2odoo(MicrosoftEvent(values))

        events = self.env["calendar.event"].search(
            [("recurrence_id", "=", recurrence.id)], order="start asc"
        )
        self.assertEqual(len(events), 3, "It should have created 3 events")
        self.assertEqual(recurrence.base_event_id, events[0])
        self.assertEqual(
            events.mapped("name"),
            ["My recurrent event", "My recurrent event", "My recurrent event"],
        )
        self.assertEqual(events[0].start, datetime(2020, 5, 3, 14, 30))
        self.assertEqual(events[0].stop, datetime(2020, 5, 3, 16, 30))
        self.assertEqual(events[1].start, datetime(2020, 5, 4, 14, 30))
        self.assertEqual(events[1].stop, datetime(2020, 5, 4, 16, 30))
        self.assertEqual(events[2].start, datetime(2020, 5, 5, 14, 30))
        self.assertEqual(events[2].stop, datetime(2020, 5, 5, 16, 30))

    @freeze_time('2020-06-03')
    def test_microsoft_recurrence_split_recurrence(self):
        values = [
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAADI/Dig=="',
                "createdDateTime": "2020-05-06T07:03:49.1444085Z",
                "lastModifiedDateTime": self.datetime_future,
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAADI/Dig==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E00800000000874F057E7423D601000000000000000010000000C6918C4B44D2D84586351FEC8B1B7F8C",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": None,
                "showAs": "busy",
                "type": "seriesMaster",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:30:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "recurrence": {
                    "pattern": {
                        "type": "daily",
                        "interval": 1,
                        "month": 0,
                        "dayOfMonth": 0,
                        "firstDayOfWeek": "sunday",
                        "index": "first",
                    },
                    "range": {
                        "type": "endDate",
                        "startDate": "2020-05-03",
                        "endDate": "2020-05-03",
                        "recurrenceTimeZone": "Romance Standard Time",
                        "numberOfOccurrences": 0,
                    },
                },
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAADI/Dkw=="',
                "createdDateTime": "2020-05-06T13:24:10.0507138Z",
                "lastModifiedDateTime": self.datetime_future,
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAADI/Dkw==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E008000000001A4457A0A923D601000000000000000010000000476AE6084FD718418262DA1AE3E41411",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": None,
                "showAs": "busy",
                "type": "seriesMaster",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAAMkgQrAAAA&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAAMkgQrAAAA",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-04T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-04T17:00:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "recurrence": {
                    "pattern": {
                        "type": "daily",
                        "interval": 1,
                        "month": 0,
                        "dayOfMonth": 0,
                        "firstDayOfWeek": "sunday",
                        "index": "first",
                    },
                    "range": {
                        "type": "endDate",
                        "startDate": "2020-05-04",
                        "endDate": "2020-05-06",
                        "recurrenceTimeZone": "Romance Standard Time",
                        "numberOfOccurrences": 0,
                    },
                },
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMj8OK"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX7vTsS0AARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAAEA==",
                "start": {"dateTime": "2020-05-03T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-03T16:30:00.0000000", "timeZone": "UTC"},
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMj8OT"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAAMkgQrAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX774WtQAAAEYAAAJAcu19N72jSr9Rp1mE2xWABwBlLa4RUBXJToExnebpwea2AAACAQ0AAABlLa4RUBXJToExnebpwea2AAAADJIEKwAAABA=",
                "start": {"dateTime": "2020-05-04T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-04T17:00:00.0000000", "timeZone": "UTC"},
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"ZS2uEVAVyU6BMZ3m6cHmtgAADI/Dkw=="',
                "createdDateTime": "2020-05-06T13:25:05.9240043Z",
                "lastModifiedDateTime": self.datetime_future,
                "changeKey": "ZS2uEVAVyU6BMZ3m6cHmtgAADI/Dkw==",
                "categories": [],
                "originalStartTimeZone": "Romance Standard Time",
                "originalEndTimeZone": "Romance Standard Time",
                "iCalUId": "040000008200E00074C5B7101A82E00807E405051A4457A0A923D601000000000000000010000000476AE6084FD718418262DA1AE3E41411",
                "reminderMinutesBeforeStart": 15,
                "isReminderOn": True,
                "hasAttachments": False,
                "subject": "My recurrent event 2",
                "bodyPreview": "",
                "importance": "normal",
                "sensitivity": "normal",
                "originalStart": "2020-05-05T14:30:00Z",
                "isAllDay": False,
                "isCancelled": False,
                "isOrganizer": True,
                "IsRoomRequested": False,
                "AutoRoomBookingStatus": "None",
                "responseRequested": True,
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAAMkgQrAAAA",
                "showAs": "busy",
                "type": "exception",
                "webLink": "https://outlook.live.com/owa/?itemid=AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX8IdBHsAARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAAMkgQrAAAAEA%3D%3D&exvsurl=1&path=/calendar/item",
                "onlineMeetingUrl": None,
                "isOnlineMeeting": False,
                "onlineMeetingProvider": "unknown",
                "AllowNewTimeProposals": True,
                "IsDraft": False,
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX8IdBHsAARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAAMkgQrAAAAEA==",
                "responseStatus": {
                    "response": "organizer",
                    "time": "0001-01-01T00:00:00Z",
                },
                "body": {"contentType": "html", "content": ""},
                "start": {"dateTime": "2020-05-05T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-05T17:00:00.0000000", "timeZone": "UTC"},
                "location": {
                    "displayName": "",
                    "locationType": "default",
                    "uniqueIdType": "unknown",
                    "address": {},
                    "coordinates": {},
                },
                "locations": [],
                "attendees": [],
                "organizer": {
                    "emailAddress": {
                        "name": "outlook_7BA43549E5FD4413@outlook.com",
                        "address": "outlook_7BA43549E5FD4413@outlook.com",
                    }
                },
            },
            {
                "@odata.type": "#microsoft.graph.event",
                "@odata.etag": 'W/"DwAAABYAAABlLa4RUBXJToExnebpwea2AAAMj8OT"',
                "seriesMasterId": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAAMkgQrAAAA",
                "type": "occurrence",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoBUQAICADX8VBriIAARgAAAkBy7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAAMkgQrAAAAEA==",
                "start": {"dateTime": "2020-05-06T14:30:00.0000000", "timeZone": "UTC"},
                "end": {"dateTime": "2020-05-06T17:00:00.0000000", "timeZone": "UTC"},
            },
        ]

        self.env["calendar.event"]._sync_microsoft2odoo(MicrosoftEvent(values))
        recurrence_1 = self.env["calendar.recurrence"].search(
            [("microsoft_id", "=", self.recurrence_id)]
        )
        recurrence_2 = self.env["calendar.recurrence"].search(
            [
                (
                    "microsoft_id",
                    "=",
                    "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAAMkgQrAAAA",
                )
            ]
        )

        events_1 = self.env["calendar.event"].search(
            [("recurrence_id", "=", recurrence_1.id)], order="start asc"
        )
        events_2 = self.env["calendar.event"].search(
            [("recurrence_id", "=", recurrence_2.id)], order="start asc"
        )
        self.assertTrue(recurrence_1, "It should have created an recurrence")
        self.assertTrue(recurrence_2, "It should have created an recurrence")
        self.assertEqual(len(events_1), 1, "It should left 1 event")
        self.assertEqual(len(events_2), 3, "It should have created 3 events")
        self.assertEqual(recurrence_1.base_event_id, events_1[0])
        self.assertEqual(recurrence_2.base_event_id, events_2[0])
        self.assertEqual(events_1.mapped("name"), ["My recurrent event"])
        self.assertEqual(
            events_2.mapped("name"),
            ["My recurrent event", "My recurrent event 2", "My recurrent event"],
        )
        self.assertEqual(events_1[0].start, datetime(2020, 5, 3, 14, 30))
        self.assertEqual(events_1[0].stop, datetime(2020, 5, 3, 16, 30))
        self.assertEqual(events_2[0].start, datetime(2020, 5, 4, 14, 30))
        self.assertEqual(events_2[0].stop, datetime(2020, 5, 4, 17, 00))
        self.assertEqual(events_2[1].start, datetime(2020, 5, 5, 14, 30))
        self.assertEqual(events_2[1].stop, datetime(2020, 5, 5, 17, 00))
        self.assertEqual(events_2[2].start, datetime(2020, 5, 6, 14, 30))
        self.assertEqual(events_2[2].stop, datetime(2020, 5, 6, 17, 00))

    @freeze_time('2020-06-03')
    def test_microsoft_recurrence_delete(self):
        recurrence_id = self.env["calendar.recurrence"].search(
            [("microsoft_id", "=", self.recurrence_id)]
        )
        event_ids = (
            self.env["calendar.event"]
            .search([("recurrence_id", "=", recurrence_id.id)], order="start asc")
            .ids
        )
        values = [
            {
                "@odata.type": "#microsoft.graph.event",
                "id": "AQ8PojGtrADQATM3ZmYAZS0yY2MAMC00MDg1LTAwAi0wMAoARgAAA0By7X03vaNKv1GnWYTbFYAHAGUtrhFQFclOgTGd5unB5rYAAAIBDQAAAGUtrhFQFclOgTGd5unB5rYAAAALLLTEAAAA",
                "@removed": {"reason": "deleted"},
            }
        ]

        self.env["calendar.event"]._sync_microsoft2odoo(MicrosoftEvent(values))

        recurrence = self.env["calendar.recurrence"].search(
            [("microsoft_id", "=", self.recurrence_id)]
        )
        events = self.env["calendar.event"].browse(event_ids).exists()
        self.assertFalse(recurrence, "It should remove recurrence")
        self.assertFalse(events, "It should remove all events")
