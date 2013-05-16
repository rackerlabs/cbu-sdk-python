import unittest

from httpretty import HTTPretty, httprettified
from requests.exceptions import HTTPError

from rcbu.client.client import Connection


class TestValidConnection(unittest.TestCase):
    def setUp(self):
        self.conn = Connection('cppcabrera', password='$x4dc4dv4d$')

    def test_connection_has_correct_properties(self):
        self.assertEqual(self.conn.token,
                         '2560cd91-bdf5-4e6d-9ae8-a33444e84b22')
        self.assertEqual(self.conn.endpoint,
                         'https://backup.api.rackspacecloud.com/v1.0')

    def test_agents_acquired(self):
        agents = self.conn.agents
        self.assertIsNotNone(agents)
        self.assertIsNot(agents, [])

    def test_backup_configurations_acquired(self):
        configs = self.conn.backup_configurations
        self.assertIsNotNone(configs)
        self.assertIsNot(configs, [])

    def test_host(self):
        self.assertEqual(self.conn.host,
                         'https://backup.api.rackspacecloud.com/v1.0')

    def test_version(self):
        self.assertEqual(self.conn.api_version, '1.0')

    def test_version_tuple(self):
        self.assertEqual(self.conn.api_version_tuple, (1, 0))

    def test_active_backups(self):
        backups = self.conn.active_backups
        self.assertIsNotNone(backups)
        self.assertIsNot(backups, [])

    def test_active_restores(self):
        restores = self.conn.active_restores
        self.assertIsNotNone(restores)
        self.assertIsNot(restores, [])
