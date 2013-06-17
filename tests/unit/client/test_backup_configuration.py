import json
import unittest

from httpretty import HTTPretty, httprettified

from rcbu.client.connection import Connection
from rcbu.common.constants import IDENTITY_TOKEN_URL
import tests.mock.auth as mock_auth
import tests.mock.configuration as mock_config
import rcbu.client.backup_configuration as backup_config
from rcbu.common.exceptions import (
    DisconnectedError, InconsistentInclusionsError
)


def _mock_auth(status):
    reply = mock_auth.authenticate()
    HTTPretty.register_uri(HTTPretty.POST, IDENTITY_TOKEN_URL,
                           status=status, body=json.dumps(reply))


def _mock_config(status, endpoint, config_id):
    reply = mock_config.backup_configuration(config_id)
    url = '{0}/{1}/{2}'.format(endpoint, 'backup-configuration', config_id)
    HTTPretty.register_uri(HTTPretty.GET, url, json.dumps(reply))


def _quick_config(connection=None):
    return backup_config.from_dict(mock_config.backup_configuration(),
                                   connection=connection)


class TestLoadBackupConfiguration(unittest.TestCase):
    def test_from_dict_works_as_expected(self):
        body = mock_config.backup_configuration()
        config = backup_config.from_dict(body)
        self.assertEqual(config.id, 0)
        self.assertEqual(config.agent_id, 1)
        self.assertEqual(config.notify_on_failure, True)
        self.assertEqual(config.notify_on_success, False)
        self.assertEqual(config.email,
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
                backup_config.from_dict(mock)


class TestBackupConfiguration(unittest.TestCase):
    @httprettified
    def setUp(self):
        _mock_auth(200)
        self.connection = Connection(username='a', password='a')
        config_api = mock_config.backup_configuration()
        self.config = backup_config.from_dict(config_api, self.connection)

    def test_id_matches_expected(self):
        self.assertEqual(self.config.id, 0)

    def test_agent_id_matches_expected(self):
        self.assertEqual(self.config.agent_id, 1)

    def test_name_matches_expected(self):
        self.assertEqual(self.config.name, 'mock')

    def test_notification_settings_match_expected(self):
        self.assertEqual(self.config.email, 'mock@mock.com')
        self.assertEqual(self.config.notify_on_success, False)
        self.assertEqual(self.config.notify_on_failure, True)

    def test_enabled_matches_expected(self):
        self.assertEqual(self.config.enabled, True)

    def test_encrypted_matches_expected(self):
        self.assertEqual(self.config.encrypted, False)

    def test_deleted_matches_expected(self):
        self.assertEqual(self.config.deleted, False)

    def test_update_notification_settings_works(self):
        self.config.update_notification_settings(email='woot',
                                                 notify_on_failure=False,
                                                 notify_on_success=True)
        self.assertEqual(self.config.email, 'woot')
        self.assertEqual(self.config.notify_on_success, True)
        self.assertEqual(self.config.notify_on_failure, False)

    def test_rename_works(self):
        self.config.rename('woot')
        self.assertEqual(self.config.name, 'woot')

    def test_disconneted_error_raised_if_no_connection(self):
        self.config.connect(None)
        with self.assertRaises(DisconnectedError):
            self.config.enable()

    @httprettified
    def _test_toggle(self, enabled=True):
        url = '{0}/{1}/{2}/{3}'.format(self.connection.host,
                                       'backup-configuration', 'enable',
                                       self.config.id)
        HTTPretty.register_uri(HTTPretty.POST, url, status=200,
                               body=json.dumps({'IsActive': enabled}))
        if enabled:
            self.config.enable()
        else:
            self.config.disable()
        self.assertEqual(self.config.enabled, enabled)

    def test_disable_works(self):
        self._test_toggle(enabled=False)

    def test_enable_works(self):
        self._test_toggle(enabled=True)

    @httprettified
    def test_delete_works(self):
        url = '{0}/backup-configuration/{1}'.format(self.connection.host,
                                                    self.config.id)
        HTTPretty.register_uri(HTTPretty.DELETE, url, status=204)
        self.assertEqual(self.config.deleted, False)
        self.config.delete()
        self.assertEqual(self.config.deleted, True)

    def test_excluding_nonexistent_path_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            self.config.exclude('not_found')

