import datetime
import unittest

import rcbu.common.activity as activity
import tests.mock.activity as mock_activity


class TestActivity(unittest.TestCase):
    def setUp(self):
        self.activity = activity.from_dict(mock_activity.activity())

    def _matches_expected(self, prop, expected):
        value = getattr(self.activity, prop)
        self.assertEqual(value, expected)

    def test_id_matches_expected(self):
        self._matches_expected('id', 1)

    def test_type_matches_expected(self):
        self._matches_expected('type', 'Backup')

    def test_parent_matches_expected(self):
        self._matches_expected('parent', 2)

    def test_name_matches_expected(self):
        self._matches_expected('name', 'mock')

    def test_deleted_matches_expected(self):
        self._matches_expected('deleted', False)

    def test_source_matches_expected(self):
        self._matches_expected('source', 'mock 3')

    def test_destination_matches_expected(self):
        self._matches_expected('destination', None)
        self.activity._type = 'Restore'
        self._matches_expected('destination', 'mock 4')

    def test_state_matches_expected(self):
        self._matches_expected('state', 'Completed')

    def test_time_matches_expected(self):
        timestamp = int('/Date(1351118760000)/'[6:16])
        self._matches_expected('time',
                               datetime.datetime.fromtimestamp(timestamp))

    def test_repr_matches_expected(self):
        actual_form = repr(self.activity)
        expected_form = ('<BackupActivity id:1 name:mock state:Completed'
                         ' time:{0}>')
        self.assertEqual(actual_form,
                         expected_form.format(self.activity.time.isoformat()))
