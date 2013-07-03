from random import randint

from rcbu.common.assertions import assert_bounded, assert_is_none
from rcbu.common.weekdays import Weekdays


class ScheduleFrequency(object):
    """A mock enum (PEP 435) for supported schedule frequencies."""
    Manual = 0
    Monthly = 1
    Weekly = 2
    Daily = 3
    Hourly = 4

    _to_api = {Manual: "Manually",
               Weekly: "Weekly",
               Daily: "Daily",
               Hourly: "Hourly",
               Monthly: "Monthly"}

    @classmethod
    def to_api(cls, value):
        return ScheduleFrequency._to_api.get(value, None)


def _validate_manual(interval, day_of_week, hour, minute):
    assert_is_none('Hourly interval', interval)
    assert_is_none('Day of week', day_of_week)
    assert_is_none('Hour', hour)
    assert_is_none('Minute', minute)


def _validate_weekly(interval, day_of_week, hour, minute):
    assert_is_none('Hourly interval', interval)
    assert_bounded('Day of week', 0, 6, day_of_week)
    assert_bounded('Hour', 0, 23, hour)
    assert_bounded('Minute', 0, 59, minute)


def _validate_daily(interval, day_of_week, hour, minute):
    assert_is_none('Hourly interval', interval)
    assert_is_none('Day of week', day_of_week)
    assert_bounded('Hour', 0, 23, hour)
    assert_bounded('Minute', 0, 59, minute)


def _validate_hourly(interval, day_of_week, hour, minute):
    assert_bounded('Hourly interval', 1, 23, interval)
    assert_is_none('Day of week', day_of_week)
    assert_is_none('Hour', hour)
    assert_is_none('Minute', minute)


# encode the validation process as a dictionary of valid schedule frequencies
_validate_fn = {
    ScheduleFrequency.Manual: _validate_manual,
    ScheduleFrequency.Weekly: _validate_weekly,
    ScheduleFrequency.Daily: _validate_daily,
    ScheduleFrequency.Hourly: _validate_hourly
}


class Schedule(object):
    """A class to simplify the management of RCBU backup scheduling."""
    def __init__(self, frequency, interval=None, day_of_week=None,
                 hour=None, minute=None):
        """
        args:
          frequency: Any value exposed by :see: ScheduleFrequency
          interval: For hourly backups - how many hours
                    between backups [0 - 23]
          day_of_week: Any value exposed by :see: rcbu.common.weekdays.Weekdays
          hour: For daily/weekly backups: the hour to
                schedule the backup [0 - 23]
          minute: For daily/weekly/hourly backups: the minute to
                  schedule the backup [0 - 59]
        raises:
          ValueError: for any argument out of range
        """
        self._validate(frequency, interval, day_of_week, hour, minute)
        self._frequency = frequency
        self._interval = interval
        self._day_of_week = day_of_week
        self._hour = hour
        self._minute = minute

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        form = ('<Schedule frequency:{0} weekday:{1} time:{2}')
        time = None
        if None not in (self.hour, self.minute):
            _form = '{0:02}:{1:02} {2}'
            time = _form.format(self.hour, self.minute, self.period)
        else:
            time = '*'
        weekday = self.weekday if self._day_of_week is not None else '*'
        form += (' every {0} hours'.format(self.interval) if self.interval else
                 '')
        form += '>'
        return form.format(self.frequency, weekday, time)

    @property
    def frequency(self):
        """Returns the frequency in a way that the API understand."""
        return ScheduleFrequency.to_api(self._frequency)

    @property
    def interval(self):
        """Returns the hourly interval used for this schedule."""
        return self._interval

    @property
    def weekday(self):
        """Returns the day of the week this schedule uses."""
        if self._day_of_week is None:
            return None
        return Weekdays.str(self._day_of_week)

    @property
    def hour(self):
        """Adjusts the hour to a 12-hour clock."""
        if self._hour is None:
            return None
        return self._hour if self._hour < 12 else self._hour - 12

    @property
    def minute(self):
        """Returns the minute this schedule uses."""
        return self._minute

    @property
    def period(self):
        """Returns 'AM' or 'PM', depending on the value of the hour."""
        if self._hour is None:
            return None
        return "AM" if self._hour < 12 else "PM"

    def _validate(self, frequency, interval, day_of_week, hour, minute):
        """Ensures that schedule args are valid, checking
        all the corner cases and all the boundaries."""
        assert_bounded('Frequency', 0, 4, frequency)
        _validate_fn[frequency](interval, day_of_week, hour, minute)

    def to_api(self):
        """Returns this schedule in a format that the API
        understands."""
        return {
            "Frequency": self.frequency,
            "StartTimeHour": self.hour,
            "StartTimeMinute": self.minute,
            "StartTimeAmPm": self.period,
            "DayOfWeekId": self._day_of_week,
            "HourInterval": self.interval
        }


def manually():
    """Returns a schedule appropriate for establishing a manual backup."""
    return Schedule(ScheduleFrequency.Manual, None, None, None, None)


def weekly(day_of_week,
           hour=None, minute=None):
    """Returns a schedule appropriate for establishing a weekly backup.

    args:
      day_of_week: On what day of the week should this
                   backup run? [Sunday - Saturday]
      hour: On what hour should this backup run? [0 - 23]
      minute: On what minute should this backup run? [0 - 59]
    """
    hour_ = randint(0, 23) if hour is None else hour
    minute_ = randint(0, 59) if minute is None else minute
    return Schedule(ScheduleFrequency.Weekly, None,
                    day_of_week=day_of_week, hour=hour_, minute=minute_)


def daily(hour=None, minute=None):
    """Returns a schedule appropriate for establishing a daily backup.

    args:
      hour: On what hour should this backup run? [0 - 23]
      minute: On what minute should this backup run? [0 - 59]
    """
    hour_ = randint(0, 23) if hour is None else hour
    minute_ = randint(0, 59) if minute is None else minute
    return Schedule(ScheduleFrequency.Daily, None,
                    day_of_week=None, hour=hour_, minute=minute_)


def hourly(interval):
    """Returns a schedule appropriate for establishing an hourly backup.

    args:
      interval: Hourly interval - every how many hours should
                this backup run? [0 - 23]
      minute: On what minute should this backup run? [0 - 59]
    """
    return Schedule(ScheduleFrequency.Hourly, interval=interval,
                    day_of_week=None, hour=None, minute=None)


def from_dict(resp):
    freq = resp['Frequency']
    minute = resp['StartTimeMinute']
    hour_ = resp['StartTimeHour']
    am_pm = resp['StartTimeAmPm']
    hour = hour_ + 12 if am_pm == 'PM' else hour_
    interval = resp['HourInterval']
    weekday_id = resp['DayOfWeekId']

    if freq == 'Manually':
        return manually()
    elif freq == 'Weekly':
        return weekly(weekday_id, hour, minute)
    elif freq == 'Daily':
        return daily(hour, minute)
    elif freq == 'Hourly':
        return hourly(interval)
    else:
        form = 'Invalid frequency {0}'.format(freq)
        raise ValueError(form)
