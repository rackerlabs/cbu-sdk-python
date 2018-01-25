import unittest
from functools import partial

import rcbu.common.schedule as schedule
import tests.mock.schedule as mock_schedule


class TestSchedule(unittest.TestCase):
    def _check(self, val, xval):
        checker = (partial(self.assertEqual, second=xval) if xval is not None
                   else self.assertIsNone)
        return checker(val)

    def _expect(self, sched, xfrequency=None, xinterval=None,
                xweekday=None, xhour=None, xperiod=None, xminute=None):
        self._check(sched.frequency, xfrequency)
        self._check(sched.interval, xinterval)
        self._check(sched.weekday, xweekday)
        self._check(sched.hour, xhour)
        self._check(sched.period, xperiod)
        self._check(sched.minute, xminute)

    def test_manual_schedule_works(self):
        sched = schedule.manually()
        self._expect(sched, 'Manually')

    def test_weekly_schedule_works(self):
        sched = schedule.weekly(0, 1, 1)
        self._expect(sched, 'Weekly',
                     xweekday='Sunday', xhour=1, xminute=1,
                     xperiod='AM')

    def test_daily_schedule_works(self):
        sched = schedule.daily(1, 1)
        self._expect(sched, 'Daily',
                     xhour=1, xminute=1, xperiod='AM')

    def test_hourly_schedule_works(self):
        sched = schedule.hourly(2)
        self._expect(sched, 'Hourly', xinterval=2)

    def test_load_manual_schedule_works(self):
        mock = mock_schedule.schedule(schedule.ScheduleFrequency.Manual)
        sched = schedule.from_dict(mock)
        self._expect(sched, 'Manually')

    def test_load_weekly_schedule_works(self):
        mock = mock_schedule.schedule(schedule.ScheduleFrequency.Weekly,
                                      weekday=0, hour=0, minute=15)
        sched = schedule.from_dict(mock)
        self._expect(sched, 'Weekly', xweekday='Sunday',
                     xhour=0, xperiod='AM', xminute=15)

    def test_load_daily_schedule_works(self):
        mock = mock_schedule.schedule(schedule.ScheduleFrequency.Daily,
                                      hour=13, minute=15)
        sched = schedule.from_dict(mock)
        self._expect(sched, 'Daily',
                     xhour=1, xperiod='PM', xminute=15)

    def test_load_hourly_schedule_works(self):
        mock = mock_schedule.schedule(schedule.ScheduleFrequency.Hourly,
                                      interval=4)
        sched = schedule.from_dict(mock)
        self._expect(sched, 'Hourly',
                     xinterval=4)

    def test_load_unknown_schedule_raises(self):
        mock = mock_schedule.schedule(8)
        with self.assertRaises(ValueError):
            schedule.from_dict(mock)

    def test_manual_repr_matches_expected(self):
        sched = schedule.manually()
        self.assertEqual(repr(sched),
                         '<Schedule frequency:Manually weekday:* time:*>')

    def test_weekly_repr_matches_expected(self):
        sched = schedule.weekly(0, 1, 1)
        self.assertEqual(repr(sched),
                         ('<Schedule frequency:Weekly weekday:Sunday '
                          'time:01:01 AM>'))

    def test_daily_repr_matches_expected(self):
        sched = schedule.daily(13, 15)
        self.assertEqual(repr(sched),
                         ('<Schedule frequency:Daily weekday:* '
                          'time:01:15 PM>'))

    def test_hourly_repr_matches_expected(self):
        sched = schedule.hourly(12)
        self.assertEqual(repr(sched),
                         ('<Schedule frequency:Hourly weekday:* '
                          'time:* every 12 hours>'))
