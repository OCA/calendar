from odoo import fields
from odoo.tests.common import TransactionCase


class TestRecurrence(TransactionCase):
    def test_weekend_days(self):
        self.env["calendar.event"].create(
            {
                "name": "Last weekend day",
                "start": fields.Datetime.to_datetime("2023-09-01 12:00:00"),
                "stop": fields.Datetime.to_datetime("2023-09-01 13:00:00"),
                "recurrency": True,
                "rrule_type": "monthly",
                "end_type": "count",
                "count": 10,
                "month_by": "day",
                "byday": "-1",
                "weekday": "weekend_day",
                "event_tz": "UTC",
            }
        )
        # You probably wonder why we get the recurrence this way,
        # it's because of this commit:
        # https://github.com/odoo/odoo/commit/43a774d68574e72fa4aabad65db42a03fac6e666
        # I had to change it to this, because the created event is
        # not the base event anymore. The same goes for the other ones
        recurrence = self.env["calendar.recurrence"].search(
            [], limit=1, order="id desc"
        )
        self.assertEqual(len(recurrence.calendar_event_ids), 10)

        first_recurrence = recurrence.calendar_event_ids.filtered(
            lambda e: e.start == fields.Datetime.to_datetime("2023-09-30 12:00:00")
            and e.stop == fields.Datetime.to_datetime("2023-09-30 13:00:00")
        )
        self.assertEqual(
            len(first_recurrence),
            1,
            "First recurrence should be on 2023-09-30 12:00:00 to 2023-09-30 13:00:00",
        )

        some_other_recurrence = recurrence.calendar_event_ids.filtered(
            lambda e: e.start == fields.Datetime.to_datetime("2024-01-28 12:00:00")
            and e.stop == fields.Datetime.to_datetime("2024-01-28 13:00:00")
        )
        self.assertEqual(
            len(some_other_recurrence),
            1,
            "A recurrence should be on 2024-01-28 12:00:00 to 2024-01-28 13:00:00",
        )

    def test_day(self):
        self.env["calendar.event"].create(
            {
                "name": "Fourth day",
                "start_date": fields.Date.to_date("2023-09-01"),
                "stop_date": fields.Date.to_date("2023-09-01"),
                "allday": True,
                "recurrency": True,
                "rrule_type": "monthly",
                "end_type": "count",
                "count": 20,
                "month_by": "day",
                "byday": "4",
                "weekday": "day",
                "event_tz": "UTC",
            }
        )
        recurrence = self.env["calendar.recurrence"].search(
            [], limit=1, order="id desc"
        )

        self.assertEqual(len(recurrence.calendar_event_ids), 20)
        some_recurrence = recurrence.calendar_event_ids.filtered(
            lambda e: e.start_date == fields.Date.to_date("2024-02-04")
            or e.start_date == fields.Date.to_date("2025-04-04")
        )
        self.assertEqual(
            len(some_recurrence), 2, "Recurrence should be on 2024-02-04 and 2025-04-04"
        )

    def test_weekdays(self):
        self.env["calendar.event"].create(
            {
                "name": "First workday (mo to fr)",
                "start_date": fields.Date.to_date("2023-09-10"),  # Skip for 2023-09
                "stop_date": fields.Date.to_date("2023-09-10"),
                "allday": True,
                "recurrency": True,
                "rrule_type": "monthly",
                "end_type": "end_date",
                "until": fields.Date.to_date("2025-09-01"),  # Including
                "month_by": "day",
                "byday": "1",
                "weekday": "weekday",
                "event_tz": "UTC",
                "interval": 2,  # Test interval
            }
        )
        recurrence = self.env["calendar.recurrence"].search(
            [], limit=1, order="id desc"
        )
        self.assertEqual(
            len(recurrence.calendar_event_ids), 12
        )  # For 2023-09 it shouldn't be there but for 2025-09-01 there should
        some_recurrence = recurrence.calendar_event_ids.filtered(
            lambda e: e.start_date == fields.Date.to_date("2024-09-02")
            or e.start_date == fields.Date.to_date("2025-09-01")
            or e.start_date == fields.Date.to_date("2024-10-02")
            or e.start_date == fields.Date.to_date("2023-09-01")  # Should not
        )
        self.assertEqual(
            len(some_recurrence), 2, "Recurrence should be on 2024-09-02 and 2025-09-01"
        )

    def test_multi_dates(self):
        self.env["calendar.event"].create(
            {
                "name": "Multi dates on 5th and 20th (interval 2)",
                "start_date": fields.Date.to_date("2023-09-10"),
                "stop_date": fields.Date.to_date("2023-09-10"),
                "allday": True,
                "recurrency": True,
                "rrule_type": "monthly",
                "end_type": "end_date",
                "until": fields.Date.to_date("2025-09-06"),
                "month_by": "dates",
                "day_ids": [
                    self.ref("calendar_monthly_multi.day_5"),
                    self.ref("calendar_monthly_multi.day_20"),
                ],
                "byday": "1",
                "weekday": "weekday",
                "event_tz": "UTC",
                "interval": 2,  # Test interval
            }
        )
        recurrence = self.env["calendar.recurrence"].search(
            [], limit=1, order="id desc"
        )
        self.assertEqual(len(recurrence.calendar_event_ids), 24)
        some_recurrence = recurrence.calendar_event_ids.filtered(
            lambda e: e.start_date == fields.Date.to_date("2023-11-05")
            or e.start_date == fields.Date.to_date("2023-11-20")
            or e.start_date == fields.Date.to_date("2024-09-05")
            or e.start_date == fields.Date.to_date("2023-09-20")
            or e.start_date == fields.Date.to_date("2025-09-05")
            or e.start_date == fields.Date.to_date("2025-09-20")
            or e.start_date == fields.Date.to_date("2023-09-05")  # Should not
            or e.start_date == fields.Date.to_date("2023-09-01")  # Should not
            or e.start_date == fields.Date.to_date("2023-12-20")  # Should not
        )
        self.assertEqual(
            len(some_recurrence),
            5,
            "Recurrence should be on 2023-09-20, 2023-11-05, "
            "2023-11-20, 2024-09-05, and 2025-09-05",
        )

    def test_inverse_rrule_multi_date(self):
        day_5 = self.ref("calendar_monthly_multi.day_5")
        day_20 = self.ref("calendar_monthly_multi.day_20")
        self.env["calendar.event"].create(
            {
                "name": "Multi dates on 5th and 20th (interval 2)",
                "start_date": fields.Date.to_date("2023-09-10"),
                "stop_date": fields.Date.to_date("2023-09-10"),
                "allday": True,
                "recurrency": True,
                "rrule_type": "monthly",
                "end_type": "end_date",
                "until": fields.Date.to_date("2025-09-06"),
                "month_by": "dates",
                "day_ids": [day_5, day_20],
                "byday": "1",
                "event_tz": "UTC",
            }
        )
        recurrence = self.env["calendar.recurrence"].search(
            [], limit=1, order="id desc"
        )

        multi_date_test = self.env["calendar.recurrence"].create(
            {"rrule": recurrence.rrule}
        )
        self.assertEqual(multi_date_test.month_by, "dates")
        self.assertEqual(multi_date_test.rrule_type, "monthly")
        self.assertIn(day_5, multi_date_test.day_ids.ids)
        self.assertIn(day_20, multi_date_test.day_ids.ids)
        self.assertEqual(len(multi_date_test.day_ids), 2)

    def test_inverse_rrule_weekdays(self):
        monday = self.ref("calendar_monthly_multi.MO")
        wednesday = self.ref("calendar_monthly_multi.WE")
        saturday = self.ref("calendar_monthly_multi.SA")
        sunday = self.ref("calendar_monthly_multi.SU")

        self.env["calendar.event"].create(
            {
                "name": "Weekend Day Test",
                "start_date": fields.Date.to_date("2023-09-10"),
                "stop_date": fields.Date.to_date("2023-09-10"),
                "allday": True,
                "recurrency": True,
                "rrule_type": "monthly",
                "end_type": "end_date",
                "until": fields.Date.to_date("2025-09-06"),
                "month_by": "day",
                "weekday": "weekend_day",
                "byday": "1",
                "event_tz": "UTC",
            }
        )
        recurrence = self.env["calendar.recurrence"].search(
            [], limit=1, order="id desc"
        )

        weekend_day_test = self.env["calendar.recurrence"].create(
            {"rrule": recurrence.rrule}
        )
        self.assertEqual(weekend_day_test.month_by, "day")
        self.assertEqual(weekend_day_test.rrule_type, "monthly")
        self.assertIn(saturday, weekend_day_test.weekday_ids.ids)
        self.assertIn(sunday, weekend_day_test.weekday_ids.ids)
        self.assertEqual(weekend_day_test.weekday, "weekend_day")

        self.env["calendar.event"].create(
            {
                "name": "Weekday (any day) test",
                "start_date": fields.Date.to_date("2023-09-10"),
                "stop_date": fields.Date.to_date("2023-09-10"),
                "allday": True,
                "recurrency": True,
                "rrule_type": "monthly",
                "end_type": "end_date",
                "until": fields.Date.to_date("2025-09-06"),
                "month_by": "day",
                "weekday": "day",
                "byday": "1",
                "event_tz": "UTC",
            }
        )
        recurrence = self.env["calendar.recurrence"].search(
            [], limit=1, order="id desc"
        )
        all_days_test = self.env["calendar.recurrence"].create(
            {"rrule": recurrence.rrule}
        )
        self.assertEqual(all_days_test.month_by, "day")
        self.assertEqual(all_days_test.rrule_type, "monthly")
        self.assertIn(monday, all_days_test.weekday_ids.ids)
        self.assertIn(saturday, all_days_test.weekday_ids.ids)
        self.assertIn(sunday, all_days_test.weekday_ids.ids)
        self.assertIn(wednesday, all_days_test.weekday_ids.ids)
        self.assertEqual(all_days_test.weekday, "day")

        self.env["calendar.event"].create(
            {
                "name": "Workday test",
                "start_date": fields.Date.to_date("2023-09-10"),
                "stop_date": fields.Date.to_date("2023-09-10"),
                "allday": True,
                "recurrency": True,
                "rrule_type": "monthly",
                "end_type": "end_date",
                "until": fields.Date.to_date("2025-09-06"),
                "month_by": "day",
                "weekday": "weekday",
                "byday": "1",
                "event_tz": "UTC",
            }
        )
        recurrence = self.env["calendar.recurrence"].search(
            [], limit=1, order="id desc"
        )

        workday_test = self.env["calendar.recurrence"].create(
            {"rrule": recurrence.rrule}
        )
        self.assertEqual(workday_test.month_by, "day")
        self.assertEqual(workday_test.rrule_type, "monthly")
        self.assertIn(monday, workday_test.weekday_ids.ids)
        self.assertIn(wednesday, workday_test.weekday_ids.ids)
        self.assertNotIn(sunday, workday_test.weekday_ids.ids)
        self.assertNotIn(saturday, workday_test.weekday_ids.ids)
        self.assertEqual(workday_test.weekday, "weekday")

        self.env["calendar.event"].create(
            {
                "name": "Custom test",
                "start_date": fields.Date.to_date("2023-09-10"),
                "stop_date": fields.Date.to_date("2023-09-10"),
                "allday": True,
                "recurrency": True,
                "rrule_type": "monthly",
                "end_type": "end_date",
                "until": fields.Date.to_date("2025-09-06"),
                "month_by": "day",
                "weekday": "custom",
                "weekday_ids": [monday, saturday],
                "byday": "2",
                "event_tz": "UTC",
            }
        )
        recurrence = self.env["calendar.recurrence"].search(
            [], limit=1, order="id desc"
        )

        custom_test = self.env["calendar.recurrence"].create(
            {"rrule": recurrence.rrule}
        )
        self.assertEqual(custom_test.month_by, "day")
        self.assertEqual(custom_test.rrule_type, "monthly")
        self.assertIn(monday, custom_test.weekday_ids.ids)
        self.assertIn(saturday, custom_test.weekday_ids.ids)
        self.assertNotIn(wednesday, custom_test.weekday_ids.ids)
        self.assertNotIn(sunday, custom_test.weekday_ids.ids)
        self.assertEqual(custom_test.weekday, "custom")

        self.env["calendar.event"].create(
            {
                "name": "Normal test",
                "start_date": fields.Date.to_date("2023-09-10"),
                "stop_date": fields.Date.to_date("2023-09-10"),
                "allday": True,
                "recurrency": True,
                "rrule_type": "monthly",
                "end_type": "end_date",
                "until": fields.Date.to_date("2025-09-06"),
                "month_by": "day",
                "weekday": "WED",
                "byday": "1",
                "event_tz": "UTC",
            }
        )
        recurrence = self.env["calendar.recurrence"].search(
            [], limit=1, order="id desc"
        )

        normal_test = self.env["calendar.recurrence"].create(
            {"rrule": recurrence.rrule}
        )
        self.assertEqual(normal_test.month_by, "day")
        self.assertEqual(normal_test.rrule_type, "monthly")
        self.assertIn(wednesday, normal_test.weekday_ids.ids)
        self.assertNotIn(sunday, normal_test.weekday_ids.ids)
        self.assertNotIn(monday, normal_test.weekday_ids.ids)
        self.assertNotIn(saturday, normal_test.weekday_ids.ids)
        self.assertEqual(normal_test.weekday, "WED")
