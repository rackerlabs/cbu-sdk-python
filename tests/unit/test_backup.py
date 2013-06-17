import json
import unittest

from httpretty import HTTPretty, httprettified

from rcbu.common.auth import IDENTITY_TOKEN_URL
from rcbu.client.connection import Connection
import tests.mock.auth as mock_auth
import rcbu.client.backup as backup


def _mock_auth(status):
    reply = mock_auth.authenticate()
    HTTPretty.register_uri(HTTPretty.POST, IDENTITY_TOKEN_URL,
                           status=status, body=json.dumps(reply))


class TestBackup(unittest.TestCase):
    @httprettified
    def setUp(self):
        _mock_auth(200)
        self.connection = Connection('a', 'b')
        self.cmd = backup.Backup(1, 2, connection=self.connection)

    @httprettified
    def test_start_works_and_sets_id(self):
        url = '{0}/backup/action-requested'.format(self.connection.host)
        HTTPretty.register_uri(HTTPretty.POST, url, body=json.dumps(100))
        self.cmd.start()
        self.assertEqual(self.cmd.id, 100)

    @httprettified
    def test_stop_works(self):
        url = '{0}/backup/action-requested'.format(self.connection.host)
        HTTPretty.register_uri(HTTPretty.POST, url)
        self.cmd.stop()
