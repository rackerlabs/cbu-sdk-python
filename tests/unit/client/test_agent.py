import json
import unittest
import sys

from httpretty import HTTPretty, httprettified
import mock

from rcbu.client.connection import Connection
from rcbu.client.client import Client
from rcbu.common.auth import IDENTITY_TOKEN_URL
import tests.mock.auth as mock_auth
import tests.mock.agent as agent_mock
import tests.mock.rsa as mock_rsa
import tests.mock.configuration as mock_config
import rcbu.client.agent as agent


def _mock_auth(status):
    reply = mock_auth.authenticate()
    HTTPretty.register_uri(HTTPretty.POST, IDENTITY_TOKEN_URL,
                           status=status, body=json.dumps(reply))


class TestLoadAgent(unittest.TestCase):
    '''The mock framework (in the stdlib in Python 3!) can do some
    pretty magical things. Below, we're avoiding the disk entirely
    by mocking the builtin open method and having it return our
    mock agent JSON and asserting that we parse it correctly.'''
    def test_can_parse_agent_from_json_file(self):
        m = mock.mock_open(read_data=json.dumps(agent_mock.agent()))
        open_fn_name = ('builtins.open' if sys.version_info[0] == 3 else
                        '__builtin__.open')
        with mock.patch(open_fn_name, m, create=False):
            conn_mock = mock.MagicMock()
            conn_mock.host = 'a'
            conn_mock.token = 'a'
            ag = agent.from_file('test', conn_mock)
            self.assertEqual(ag.name, 'mock')
            self.assertEqual(ag.id, '1')
            self.assertEqual(ag.os, 'linux 13.04')


class TestAgent(unittest.TestCase):
    @httprettified
    def setUp(self):
        _mock_auth(200)
        self.conn = Connection('1', 'dfw', password='3')
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

    def test_vault_size_matches_expected(self):
        self.assertEqual(self.agent.vault_size, 2 * 2 ** 30)

    @httprettified
    def test_online_fetches_from_API_if_status_unknown(self):
        url = '{0}/agent/{1}'.format(self.conn.host, self.agent.id)
        HTTPretty.register_uri(HTTPretty.GET, url, status=200,
                               body=json.dumps({'Status': 'Online'}))
        self.assertEqual(self.agent.online, True)

    @httprettified
    def test_vault_size_fetches_from_API_if_none(self):
        url = '{0}/agent/{1}'.format(self.conn.host, self.agent.id)
        HTTPretty.register_uri(HTTPretty.GET, url, status=200,
                               body=json.dumps({'BackupVaultSize': '2 GB'}))
        self.assertEqual(self.agent.vault_size, 2 * 2**30)

    def test_online_returns_correct_result(self):
        self.agent._online = 'Online'
        self.assertTrue(self.agent.online)
        self.agent._online = 'Offline'
        self.assertFalse(self.agent.online)

    @httprettified
    def test_fetch_backup_configurations_works(self):
        url = '{0}/backup-configuration/system/{1}'.format(self.conn.host,
                                                           self.agent.id)
        data = json.dumps([mock_config.backup_configuration()
                           for i in range(10)])
        HTTPretty.register_uri(HTTPretty.GET, url, status=200, body=data)
        confs = list(self.agent.backup_configurations)
        self.assertEqual(len(confs), 10)
        for conf in confs:
            self.assertEqual(conf.name, 'mock')

    @httprettified
    def test_encrypt_works(self):
        url = '{0}/agent/encrypt'.format(self.conn.host)
        HTTPretty.register_uri(HTTPretty.POST,
                               url, status=204)
        self.assertEqual(self.agent.encrypted, False)

        # This is some vicious mocking. In order:
        # 1. Mock the built-in open so we read in a mock PEM
        # 2. Mock PyCrypto's importKey so we avoid reading from /dev/urandom
        # 3. Mock PyCrypto's Cipher generator so we avoid randgen
        # 4. Mock PyCrypto's Cipher.encrypt since its already a mock
        # 5. Ensure the call can complete and the agent is encrypted
        m = mock.mock_open(read_data=mock_rsa.public_key())
        open_fn_name = ('builtins.open' if sys.version_info[0] == 3 else
                        '__builtin__.open')
        with mock.patch(open_fn_name, m, create=True):
            with mock.patch('Crypto.PublicKey.RSA.importKey') as key:
                key.return_value = 'woot'
                with mock.patch('Crypto.Cipher.PKCS1_v1_5.new') as cipher:
                    cipher.return_value = mock.MagicMock()
                    cipher.return_value.encrypt.return_value = b'awesome'
                    self.agent.encrypt('sweet_tacos')

        self.assertEqual(self.agent.encrypted, True)

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

    def test_connect_works(self):
        self.agent.connect(None)
        self.assertEqual(self.agent._connection, None)
        self.agent.connect(self.conn)
        self.assertIs(self.agent._connection, self.conn)

    @httprettified
    def test_delete_works(self):
        '''For this test, it's enough to verify that delete can be
        called without throwing any errors. This also checks that the URL
        that is called if of the expected format. If the URL fails to match,
        then it bypasses the HTTPretty mock and throws a 403.'''
        HTTPretty.register_uri(HTTPretty.POST,
                               '{0}/agent/delete'.format(self.conn.host),
                               status=204)
        self.agent.delete()
