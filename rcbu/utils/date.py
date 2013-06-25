import datetime
import re


DATE_MATCHER = re.compile(r'/Date\((\d{13})\)/')


def parse(date):
    """Given a .Net Date object, returns a Python datetime object."""
    # .Net Date objects differ in numeric format from Python datetime
    # objects. We must parse out the milliseconds instead of passing
    # the value directly to datetime, or we get a:
    # ValueError: year is out of range
    stamp = DATE_MATCHER.match(date).group(1)
    precise_timestamp = '{0}.{1}'.format(stamp[:10], stamp[10:])
    return datetime.datetime.fromtimestamp(float(precise_timestamp))
