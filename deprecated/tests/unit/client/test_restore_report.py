import unittest

import rcbu.client.restore_report as restore_report
import tests.mock.report as mock_report
from rcbu.common.exceptions import RestoreFailed


class TestRestoreReport(unittest.TestCase):
    def setUp(self):
        mock = mock_report.restore_report(errors=['explosions'])
        self.report = restore_report.from_dict(1, mock)

    def test_repr_matches_expected(self):
        form = ('<RestoreReport id:{0} state:{1} ok:{2} started:{3} '
                'duration:{4} #errors:{5} bytes:{6}>')
        self.assertEqual(repr(self.report),
                         form.format(self.report.id, self.report.state,
                                     self.report.ok,
                                     self.report.started.isoformat(),
                                     '0:00:00', len(self.report.errors),
                                     self.report.bytes_restored))

    def test_id_matches_expected(self):
        self.assertEqual(self.report.id, 1)

    def test_errors_match_expected(self):
        self.assertEqual(len(self.report.errors), 1)
        self.assertEqual(self.report.errors[0], 'explosions')

    def test_ok_matches_expected(self):
        self.assertEqual(self.report.ok, False)

    def test_raises_if_not_restorable(self):
        with self.assertRaises(RestoreFailed):
            self.report.raise_if_not_ok()

    def test_restored_matches_expected(self):
        self.assertEqual(self.report.files_restored, 0)
        self.assertEqual(self.report.bytes_restored, 2 * 2**30)

    def test_destination_matches_expected(self):
        self.assertEqual(self.report.destination, '/mock 1')
