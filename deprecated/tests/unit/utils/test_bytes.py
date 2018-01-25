import unittest

import rcbu.utils.bytes as byte_utils


class TestBytes(unittest.TestCase):
    def _core(self, input_bytestring, expected):
        self.assertEqual(byte_utils.dehumanize_bytes(input_bytestring),
                         expected)

    def test_handles_unprefixed_string(self):
        self._core('1.1', 1)

    def test_handles_kilobytes(self):
        self._core('2 KB', 2048)

    def test_handles_megabytes(self):
        self._core('3.0 Mb', 3 * 2**20)

    def test_handles_zero_gigabytes(self):
        self._core('0 gB', 0)

    def test_handles_lowercased_terabytes(self):
        self._core('234 tb', 234 * 2**40)

    def test_handles_petabytes(self):
        self._core('322 pB', 322 * 2**50)

    def test_handles_exabytes(self):
        self._core('2.13 EB', 2.13 * 2**60)

    def test_handles_zettabytes(self):
        self._core('1 ZB', 2 ** 70)

    def test_handles_yottabytes(self):
        self._core('1 YB', 2 ** 80)
