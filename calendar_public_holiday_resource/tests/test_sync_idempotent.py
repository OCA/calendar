# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

import pytz

from .common import TestPublicHolidayResourceCommon


class TestSyncIdempotent(TestPublicHolidayResourceCommon):
    """A repeated synchronisation must be a no-op, whoever runs it.

    The mirrors used to be prepared in the syncing user's timezone, relying on
    the ``hr_holidays`` create hook to land them in the calendar's -- but that
    hook never runs on write or for personal records, so the stored values
    depended on which user's sync ran last and every run rewrote the records
    again, re-evaluating every overlapping leave along the way.
    """

    def _assert_noop(self, summary):
        for key in ("created", "adopted", "updated", "removed"):
            self.assertEqual(summary[key], 0, f"{key} should be 0: {summary}")

    def test_repeat_sync_is_a_noop(self):
        self.env.user.tz = "America/New_York"
        line = self._create_line(date(self.year, 10, 3))
        self._assert_noop(line._sync_global_leaves())

    def test_sync_under_another_timezone_is_a_noop(self):
        self.env.user.tz = "America/New_York"
        line = self._create_line(date(self.year, 10, 3))
        self.env.user.tz = "Asia/Tokyo"
        self._assert_noop(line._sync_global_leaves())
        self.env.user.tz = False
        self._assert_noop(line._sync_global_leaves())

    def test_regional_mirror_spans_the_resource_local_day(self):
        self.env.user.tz = "America/New_York"
        self._set_calendar_regions(self.cal_by, self.region_by)
        resource = self._resources_by_calendar[self.cal_by.id]
        resource.tz = "Europe/Berlin"
        day = date(self.year, 8, 15)
        line = self._create_line(day, name="Regional", regions=self.region_by)
        mirror = self.leave_model.search(
            [
                ("public_holiday_line_id", "=", line.id),
                ("resource_id", "=", resource.id),
            ]
        )
        self.assertEqual(len(mirror), 1)
        tz = pytz.timezone("Europe/Berlin")
        start = pytz.utc.localize(mirror.date_from).astimezone(tz)
        stop = pytz.utc.localize(mirror.date_to).astimezone(tz)
        self.assertEqual(start.date(), day)
        self.assertEqual((start.hour, start.minute), (0, 0))
        self.assertEqual(stop.date(), day)
        self.assertEqual((stop.hour, stop.minute), (23, 59))
        self._assert_noop(line._sync_global_leaves())
        self.env.user.tz = "Asia/Tokyo"
        self._assert_noop(line._sync_global_leaves())
