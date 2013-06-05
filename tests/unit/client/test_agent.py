import json
import unittest

from httpretty import HTTPretty, httprettified

from rcbu.client.connection import Connection
from rcbu.client.client import Client
from rcbu.common.auth import IDENTITY_TOKEN_URL
import tests.mock.auth as mock_auth
import tests.mock.agent as agent_mock
import rcbu.client.agent as agent


def _mock_auth(status):
    reply = mock_auth.authenticate()
    HTTPretty.register_uri(HTTPretty.POST, IDENTITY_TOKEN_URL,
                           status=status, body=json.dumps(reply))


class TestAgent(unittest.TestCase):
    @httprettified
    def setUp(self):
        _mock_auth(200)
        self.conn = Connection('1', '2')
        self.client = Client(self.conn)
        self.agent = agent.from_dict(agent_mock.agent(), self.conn)

    def test_name_matches_expected(self):
        self.assertEqual(self.agent.name, 'mock')

    def test_version_matches_expected(self):
        self.assertEqual(self.agent.version, '1.065959')

    def test_id_matches_expected(self):
        self.assertEqual(self.agent.id, '1')

    def test_os_matches_expected(self):
        self.assertEqual(self.agent.os, 'linux 13.04')

    def test_dc_matches_expected(self):
        self.assertEqual(self.agent.data_center, 'ORD')

    def test_encrypted_matches_expected(self):
        self.assertEqual(self.agent.encrypted, False)

    def test_enabled_matches_expected(self):
        self.assertEqual(self.agent.enabled, True)

    @httprettified
    def _toggle_test(self, enabled=True):
        HTTPretty.register_uri(HTTPretty.POST,
                               '{0}/agent/enable'.format(self.conn.host),
                               status=200)
        if enabled:
            self.agent.enable()
        else:
            self.agent.disable()
        self.assertEqual(self.agent.enabled, enabled)
        
    def test_enabling_agent_works(self):
        self._toggle_test(enabled=True)

    def test_disabling_agent_works(self):
        self._toggle_test(enabled=False)


        
