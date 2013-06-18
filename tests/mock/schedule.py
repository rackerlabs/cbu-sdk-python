from rcbu.common.schedule import ScheduleFrequency


def schedule(freq,
             interval=None, weekday=None,
             hour=None, minute=None, period=None):
    return {
        'Frequency': ScheduleFrequency.to_api(freq),
        'StartTimeMinute': minute,
        'StartTimeHour': hour,
        'StartTimeAmPm': period,
        'HourInterval': interval,
        'DayOfWeekId': weekday
    }
