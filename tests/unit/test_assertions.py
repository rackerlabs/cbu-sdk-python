import unittest

import rcbu.common.assertions as asserts


class TestAssertions(unittest.TestCase):
    def test_assert_is_none_throws_when_not_none(self):
        with self.assertRaises(ValueError):
            asserts.assert_is_none('test', 1)

    def test_assert_is_none_works(self):
        asserts.assert_is_none('test', None)

    def test_assert_bounded_throws_when_above_bounds(self):
        with self.assertRaises(ValueError):
            asserts.assert_bounded('test', 1, 3, 4)

    def test_assert_bounded_throws_when_below_bounds(self):
        with self.assertRaises(ValueError):
            asserts.assert_bounded('test', 1, 3, 0)

    def test_assert_bounded_works(self):
        [asserts.assert_bounded('test', 1, 3, i) for i in range(1, 4)]
