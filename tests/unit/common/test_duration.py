import unittest

import rcbu.common.duration as duration


class TestDuration(unittest.TestCase):
    def test_not_integer_seconds_throws_value_error(self):
        cases = ('10:10:aa', '10:aa:10', 'aa:10:10', '0:00:60', '0:60:00')
        for case in cases:
            with self.assertRaises(ValueError):
                duration.seconds(case)

    def test_seconds_works(self):
        cases = (  # string, seconds
            ('0:00:00', 0),
            ('0:00:01', 1),
            ('0:01:00', 60),
            ('1:00:00', 3600),
            ('23:59:59', 86399),
            ('1024:00:00', 3686400)
        )
        for case in cases:
            self.assertEqual(duration.seconds(case[0]), case[1])

    def test_tuple_works(self):
        cases = (  # value, hours, minutes, seconds
            (0, 0, 0, 0),
            (1, 0, 0, 1),
            (60, 0, 1, 0),
            (3600, 1, 0, 0),
            (86399, 23, 59, 59),
            (3686400, 1024, 0, 0)
        )
        for case in cases:
            self.assertEqual(duration.tuple(case[0]), tuple(case[1:]))
