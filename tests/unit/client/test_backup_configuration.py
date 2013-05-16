import json
import unittest

from httpretty import HTTPretty, httprettified

from rcbu.client.client import Connection
from rcbu.common.constants import IDENTITY_TOKEN_URL
from tests.mock.auth import authenticate
from tests.mock.configuration import backup_configuration


def _mock_auth(status):
    reply = authenticate()
    HTTPretty.register_uri(HTTPretty.POST, IDENTITY_TOKEN_URL,
                           status=status, body=json.dumps(reply))


def _mock_config(status, endpoint, config_id):
    reply = backup_configuration()
    url = '{}/{}/{}'.format(endpoint, 'backup-configuration', config_id)
    HTTPretty.register_uri(HTTPretty.GET, url, json.dumps(reply))


class TestBackupConfiguration(unittest.TestCase):
    @httprettified
    def setUp(self):
        _mock_auth(200)
        self.connection = Connection(username='a', password='a')

        _mock_config(200, self.connection.host, 1)
        self.config = self.connection.get_backup_configuration(1)
