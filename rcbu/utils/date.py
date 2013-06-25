import datetime


def parse(date):
    """Given a .Net Date object, returns a Python datetime object."""
    timestamp = int(date[6:16])
    return datetime.datetime.fromtimestamp(timestamp)
