import json
import unittest

from httpretty import HTTPretty, httprettified
from requests.exceptions import HTTPError
from dateutil import parser

from rcbu.client.connection import Connection
from rcbu.client.client import Client
from rcbu.common.constants import IDENTITY_TOKEN_URL
from tests.mock.auth import (
    authenticate, MOCK_ENDPOINT_STRIPPED, MOCK_KEY
)


def _mock_auth(status):
    reply = authenticate()
    HTTPretty.register_uri(HTTPretty.POST, IDENTITY_TOKEN_URL,
                           status=status, body=json.dumps(reply))


class TestValidConnection(unittest.TestCase):

    @httprettified
    def setUp(self):
        _mock_auth(200)
        self.conn = Connection('a', password='a')
        self.client = Client(self.conn)

    def test_connection_has_correct_properties(self):
        self.assertEqual(self.conn.token, MOCK_KEY)
        self.assertEqual(self.conn.host, MOCK_ENDPOINT_STRIPPED)

    @httprettified
    def test_agents_raises_403_on_invalid_auth(self):
        url = self.conn.host + '/user/agents'
        HTTPretty.register_uri(HTTPretty.GET, url, status=403)
        with self.assertRaises(HTTPError):
            self.client.agents

    @httprettified
    def test_backup_configurations_raises_403_on_invalid_auth(self):
        url = self.conn.host + '/backup-configuration'
        HTTPretty.register_uri(HTTPretty.GET, url, status=403)
        with self.assertRaises(HTTPError):
            self.client.backup_configurations

    def test_repr_matches_expected(self):
        form = ('<Connection host:{0} tenant:{1} username:{2} expires:{3}>')
        self.assertEqual(repr(self.conn),
                         form.format(self.conn.host, self.conn.tenant,
                                     self.conn.username,
                                     self.conn.expires.isoformat()))

    def test_host(self):
        self.assertEqual(self.conn.host, MOCK_ENDPOINT_STRIPPED)

    def test_version(self):
        self.assertEqual(self.conn.api_version, '1.0')

    def test_version_tuple(self):
        self.assertEqual(self.conn.api_version_tuple, (1, 0))

    def test_tenant_matches_expected(self):
        self.assertEqual(self.conn.tenant, 111111)

    def test_expires_matches_expected(self):
        self.assertEqual(self.conn.expires,
                         parser.parse(self.conn._expiry))
