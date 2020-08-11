# Copyright 2017 Laslabs Inc.
# Copyright 2018 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from mock import patch

from odoo import fields

from .setup import Setup, datetime_str, datetime_tz


MOCK_DATETIME = 'odoo.addons.calendar_resource.tests.test_calendar_event.'\
                'fields.Datetime.now'


class TestSetup(Setup):

    @patch(MOCK_DATETIME)
    def test_get_datetime_interval_day_weekday_later(self, mock_datetime):
        """ Ensure returns future weekday later in week """
        mock_datetime.return_value = datetime_str(2017, 6, 28, 12, 0, 0)
        res = self._get_datetime_interval(
            3, '12:00:00',
            4, '13:00:00',
        )
        exp = (datetime_str(2017, 8, 3, 12, 0, 0), datetime_str(2017, 8, 4, 13, 0, 0))
        self.assertEqual(
            res,
            exp,
        )

    @patch(MOCK_DATETIME)
    def test_get_datetime_interval_day_weekday_previous(self, mock_datetime):
        """ Ensure returns future weekday sooner in week """
        mock_datetime.return_value = datetime_str(2016, 5, 6, 12, 0, 0)
        res = self._get_datetime_interval(
            0, '12:00:00',
            1, '13:00:00',
        )
        exp = (datetime_str(2016, 6, 6, 12, 0, 0), datetime_str(2016, 6, 7, 13, 0, 0))
        self.assertEqual(
            res,
            exp,
        )

    @patch(MOCK_DATETIME)
    def test_get_datetime_interval_day_same_weekday(self, mock_datetime):
        """ Ensure returns future weekday same weekday """
        mock_datetime.return_value = datetime_str(2016, 5, 2, 12, 0, 0)
        res = self._get_datetime_interval(
            0, '12:00:00',
            0, '13:00:00',
        )
        exp = (datetime_str(2016, 6, 6, 12, 0, 0), datetime_str(2016, 6, 6, 13, 0, 0))
        self.assertEqual(
            res,
            exp,
        )

    # def test_intervals_to_dt(self):
    #     """ Test changes string to datetime """
    #     interval = [(datetime_tz(2017, 3, 7, 0, 0, 0), datetime_tz(2017, 3, 7, 16, 0, 0))]
    #     exp = [(
    #         fields.Datetime.from_string(interval[0][0]),
    #         fields.Datetime.from_string(interval[0][1]),
    #     )]
    #     # res = self._intervals_to_dt(interval)
    #     self.assertEqual(
    #         exp, interval
    #     )
