import unittest
import json

import mock

import rcbu.client.restore as restore
import tests.mock.restore as mock_restore


class TestRestoreLoad(unittest.TestCase):
    def test_restore_from_dict_works(self):
        mock = mock_restore.restore()
        restore_obj = restore.from_dict(mock)
        self.assertEqual(restore_obj.overwrite, False)
        self.assertEqual(restore_obj.id, 1)
        self.assertEqual(restore_obj.state, 'Unknown')
