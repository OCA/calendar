# Copyright 2017 Laslabs Inc.
# Copyright 2018 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .setup import Setup, datetime_tz


class TestResourceCalendar(Setup):

    def test_get_unavailable_intervals_outside_both(self):
        """ Test returns intervals event outside both """
        start = datetime_tz(2017, 3, 6, 0, 0, 0)
        end = datetime_tz(2017, 3, 12, 23, 59, 59)
        exp = [
            (datetime_tz(2017, 3, 6, 0, 0, 0), datetime_tz(2017, 3, 7, 0, 0, 0)),
            (datetime_tz(2017, 3, 8, 16, 0, 0), datetime_tz(2017, 3, 9, 9, 0, 0)),
            (datetime_tz(2017, 3, 10, 0, 0, 0), datetime_tz(2017, 3, 13, 0, 0, 0)),
        ]
        # exp = self._intervals_to_dt(exp)
        self.assertEqual(
            exp,
            self.Calendar._get_unavailable_intervals(
                self.intervals,
                start.date(),
                end.date(),
            )
        )

    def test_get_conflicting_intervals_inside_both(self):
        """ Test returns intervals event inside both """
        start = datetime_tz(2017, 3, 8, 17, 0, 0)
        end = datetime_tz(2017, 3, 9, 8, 0, 0)
        exp = [
            (datetime_tz(2017, 3, 8, 16, 0, 0), datetime_tz(2017, 3, 9, 9, 0, 0))
        ]
        self.assertEqual(
            exp,
            self.Calendar._get_conflicting_unavailable_intervals(
                self.intervals,
                start,
                end,
            )
        )

    def test_get_conflicting_intervals_overlap_inside_left(self):
        """ Test returns intervals event overlap left """
        start = datetime_tz(2017, 3, 7, 10, 0, 0)
        end = datetime_tz(2017, 3, 9, 6, 0, 0)
        exp = [
            (datetime_tz(2017, 3, 8, 16, 0, 0), datetime_tz(2017, 3, 9, 9, 0, 0)),
        ]
        self.assertEqual(
            exp,
            self.Calendar._get_conflicting_unavailable_intervals(
                self.intervals,
                start,
                end,
            )
        )

    def test_get_conflicting_intervals_overlap_outside_left(self):
        """ Test returns intervals event overlap left """
        start = datetime_tz(2017, 3, 6, 10, 0, 0)
        end = datetime_tz(2017, 3, 7, 6, 0, 0)
        exp = [
            (datetime_tz(2017, 3, 6, 0, 0, 0), datetime_tz(2017, 3, 7, 0, 0, 0)),
        ]
        self.assertEqual(
            exp,
            self.Calendar._get_conflicting_unavailable_intervals(
                self.intervals,
                start,
                end,
            )
        )

    def test_get_unavailable_intervals_match_right(self):
        """ Test returns intervals event match right """
        start = datetime_tz(2017, 3, 9, 9, 0, 0)
        end = datetime_tz(2017, 3, 10, 0, 0, 0)
        exp = [
            (datetime_tz(2017, 3, 8, 16, 0, 0), datetime_tz(2017, 3, 9, 9, 0, 0)),
            (datetime_tz(2017, 3, 10, 0, 0, 0), datetime_tz(2017, 3, 11, 0, 0, 0)),
        ]
        self.assertEqual(
            exp,
            self.Calendar._get_unavailable_intervals(
                self.intervals,
                start,
                end,
            )
        )

    def test_get_conflicting_intervals_match_right(self):
        """ Test returns intervals event match right """
        start = datetime_tz(2017, 3, 9, 9, 0, 0)
        end = datetime_tz(2017, 3, 10, 0, 0, 0)
        self.assertFalse(
            self.Calendar._get_conflicting_unavailable_intervals(
                self.intervals,
                start,
                end,
            )
        )

    def test_clean_datetime_intervals(self):
        """ Test overlaps correctly removed """
        res = self.Calendar._clean_datetime_intervals(self.intervals)
        exp = self.cleaned_intervals
        self.assertEqual(
            res,
            exp,
            'Intervals are not equal.\nRes:\n%s\nExpect:\n%s' % (res, exp),
        )
