import json
import unittest

from httpretty import HTTPretty, httprettified

from rcbu.common.auth import IDENTITY_TOKEN_URL
from rcbu.client.connection import Connection
import tests.mock.auth as mock_auth
import tests.mock.restore as mock_restore
import rcbu.client.restore as restore


def _mock_auth(status):
    reply = mock_auth.authenticate()
    HTTPretty.register_uri(HTTPretty.POST, IDENTITY_TOKEN_URL,
                           status=status, body=json.dumps(reply))


class TestRestore(unittest.TestCase):
    @httprettified
    def setUp(self):
        _mock_auth(200)
        self.connection = Connection('a', 'b')
        self.cmd = restore.Restore(1, connection=self.connection)

    @httprettified
    def test_start_works(self):
        url = '{0}/restore/action-requested'.format(self.connection.host)
        HTTPretty.register_uri(HTTPretty.POST, url)
        self.cmd.start()

    @httprettified
    def test_start_encrypted_works(self):
        url = '{0}/restore/action-requested'.format(self.connection.host)
        HTTPretty.register_uri(HTTPretty.POST, url)
        self.cmd._encrypted = True
        self.cmd._encrypted_password = 'taco'
        self.cmd.start()

    @httprettified
    def test_stop_works(self):
        url = '{0}/restore/action-requested'.format(self.connection.host)
        HTTPretty.register_uri(HTTPretty.POST, url)
        self.cmd.stop()


class TestRestoreLoad(unittest.TestCase):
    def test_restore_from_dict_works(self):
        mock = mock_restore.restore()
        restore_obj = restore.from_dict(mock)
        self.assertEqual(restore_obj.overwrites, False)
        self.assertEqual(restore_obj.id, 1)
        self.assertEqual(restore_obj.state, 'Unknown')
