import unittest

import mock

from rcbu.utils.perf import Timer


class TestTimer(unittest.TestCase):
    def test_elapsed_time_is_correct(self):
        with mock.patch('time.time') as time_mock:
            time_mock.return_value = 10
            with Timer() as t:
                time_mock.return_value = 11
            self.assertEqual(t.elapsed, 1)
