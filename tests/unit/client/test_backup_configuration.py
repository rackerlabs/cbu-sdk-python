import json
import unittest

from httpretty import HTTPretty, httprettified

from rcbu.client.connection import Connection
from rcbu.common.constants import IDENTITY_TOKEN_URL
import tests.mock.auth as mock_auth
import tests.mock.configuration as mock_config
import rcbu.client.backup_configuration as bconf


def _mock_auth(status):
    reply = mock_auth.authenticate()
    HTTPretty.register_uri(HTTPretty.POST, IDENTITY_TOKEN_URL,
                           status=status, body=json.dumps(reply))


def _mock_config(status, endpoint, config_id):
    reply = mock_config.backup_configuration(config_id)
    url = '{0}/{1}/{2}'.format(endpoint, 'backup-configuration', config_id)
    HTTPretty.register_uri(HTTPretty.GET, url, json.dumps(reply))


def _quick_config(connection=None):
    return bconf.from_dict(mock_config.backup_configuration(),
                           connection=connection)


class TestBackupConfiguration(unittest.TestCase):
    @httprettified
    def setUp(self):
        _mock_auth(200)
        self.connection = Connection(username='a', password='a')

    def test_from_dict_works_as_expected(self):
        body = mock_config.backup_configuration()
        config = bconf.from_dict(body)
        self.assertEqual(config.id, 0)
        self.assertEqual(config.agent_id, 1)
        self.assertEqual(config.notification_settings['on_failure'], True)
        self.assertEqual(config.notification_settings['on_success'], False)
        self.assertEqual(config.notification_settings['email'],
                         'mock@mock.com')
        self.assertEqual(config.name, 'mock')
        self.assertEqual(config.encrypted, False)
        self.assertEqual(config.enabled, True)
        self.assertEqual(config.deleted, False)

    def test_from_dict_throws_key_error_when_missing_attr(self):
        data_keys = mock_config.backup_configuration().keys()
        for key in data_keys:
            mock = mock_config.backup_configuration()
            del mock[key]
            with self.assertRaises(KeyError):
                bconf.from_dict(mock)

    def test_to_json_contains_expected_fields(self):
        mock = mock_config.backup_configuration()
        config = bconf.from_dict(mock)
        parsed = json.loads(bconf.to_json(config))

        # These keys aren't needed
        del mock['IsDeleted']
        del mock['IsEncrypted']

        for key in mock.keys():
            self.assertIn(key, parsed)

    def test_update_notification_settings_works(self):
        config = _quick_config()
        config.update_notification_settings('woot',
                                            notify_on_failure=False,
                                            notify_on_success=True)
        settings = config.notification_settings
        self.assertEqual(settings['email'], 'woot')
        self.assertEqual(settings['on_success'], True)
        self.assertEqual(settings['on_failure'], False)

    def test_change_name_works(self):
        config = _quick_config()
        config.change_name('woot')
        self.assertEqual(config.name, 'woot')

    def test_disconneted_error_raised_if_no_connection(self):
        config = _quick_config()
        with self.assertRaises(bconf.DisconnectedError):
            config.enable()

    def test_connect_works(self):
        config = _quick_config()
        config.connect(self.connection)
        self.assertIs(config._connection, self.connection)

    @httprettified
    def _test_toggle(self, enabled=True):
        config = _quick_config(self.connection)
        url = '{0}/{1}/{2}/{3}'.format(self.connection.host,
                                       'backup-configuration', 'enable',
                                       config.id)
        HTTPretty.register_uri(HTTPretty.POST, url, status=200,
                               body=json.dumps({'IsActive': enabled}))
        if enabled:
            config.enable()
        else:
            config.disable()
        self.assertEqual(config.enabled, enabled)

    def test_disable_works(self):
        self._test_toggle(enabled=False)

    def test_enable_works(self):
        self._test_toggle(enabled=True)
