class Weekdays(object):
    """A mock enum. When pep 435 rolls out, this can be upgraded to be a proper
    enum.

    ref: http://www.python.org/dev/peps/pep-0435/
    """
    Sunday = 0
    Monday = 1
    Tuesday = 2
    Wednesday = 3
    Thursday = 4
    Friday = 5
    Saturday = 6

    _to_string = {
        0: 'Sunday',
        1: 'Monday',
        2: 'Tuesday',
        3: 'Wednesday',
        4: 'Thursday',
        5: 'Friday',
        6: 'Saturday'
    }

    @classmethod
    def str(cls, value):
        return cls._to_string[value]
