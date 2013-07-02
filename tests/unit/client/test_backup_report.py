import datetime
import unittest

import rcbu.client.backup_report as backup_report
import tests.mock.report as mock_report
from rcbu.common.exceptions import BackupFailed


class TestBackupReport(unittest.TestCase):
    def setUp(self):
        mock = mock_report.backup_report(errors=['explosions'],
                                         restorable=True)
        self.report = backup_report.from_dict(1, mock)

    def test_repr_matches_expected(self):
        form = ('<BackupReport id:{0} state:{1} ok:{2} started:{3} '
                'duration:{4} #errors:{5} bytes:{6}>')
        form = form.format(self.report.id, self.report.state, self.report.ok,
                           self.report.started.isoformat(), '0:00:00',
                           len(self.report.errors),
                           self.report.bytes_stored)
        self.assertEqual(repr(self.report), form)

    def test_id_matches_expected(self):
        self.assertEqual(self.report.id, 1)

    def test_state_matches_expected(self):
        self.assertEqual(self.report.state, 'Completed')

    def test_errors_match_expected(self):
        self.assertEqual(len(self.report.errors), 1)
        self.assertEqual(self.report.errors[0], 'explosions')

    def test_outcome_matches_expected(self):
        self.assertEqual(self.report.outcome, 'OK')

    def test_ok_matches_expected(self):
        self.assertEqual(self.report.ok, True)

    def test_diagnostics_matches_expected(self):
        self.assertEqual(self.report.diagnostics, 'OK')

    def test_started_matches_expected(self):
        expect = datetime.datetime.fromtimestamp(1351118760.000)
        self.assertEqual(self.report.started, expect)

    def test_ended_matches_expected(self):
        expect = datetime.datetime.fromtimestamp(1351118760.001)
        self.assertEqual(self.report.ended, expect)

    def test_duration_matches_expected(self):
        self.assertEqual(self.report.duration, 0)

    def test_does_not_raise_if_ok(self):
        self.report.raise_if_not_ok()

    def test_raises_if_not_restorable(self):
        self.report._restorable = False
        with self.assertRaises(BackupFailed):
            self.report.raise_if_not_ok()

    def test_searched_matches_expected(self):
        self.assertEqual(self.report.files_searched, 0)
        self.assertEqual(self.report.bytes_searched, 2 * 2**30)

    def test_stored_matches_expected(self):
        self.assertEqual(self.report.files_stored, 0)
        self.assertEqual(self.report.bytes_stored, 2 * 2**30)
