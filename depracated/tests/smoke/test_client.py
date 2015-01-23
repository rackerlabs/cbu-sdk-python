import unittest

from rcbu.client.connection import Connection
from rcbu.client.client import Client
from tests.utils.credentials import Credentials


class TestClientBasic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        creds = Credentials()
        cls.connection = Connection(creds.name, creds.region,
                                    apikey=creds.key)
        cls.client = Client(cls.connection)

    def setUp(self):
        self.client = TestClientBasic.client

    def test_has_agents(self):
        agents = list(self.client.agents)
        self.assertGreater(len(agents), 0)

    def test_get_agent_by_id(self):
        agent = list(self.client.agents)[-1]
        agent2 = self.client.get_agent(agent.id)
        self.assertEqual(agent.id, agent2.id)

    def test_client_can_fetch_backup_history(self):
        backups = list(self.client.backup_history)
        self.assertGreaterEqual(len(backups), 0)

    def test_client_can_fetch_restore_history(self):
        restores = list(self.client.restore_history)
        self.assertGreaterEqual(len(restores), 0)

    def test_client_can_fetch_active_backups(self):
        backups = list(self.client.active_backups)
        self.assertGreaterEqual(len(backups), 0)
        for backup in backups:
            self.assertEqual(backup.type, 'Backup')

    def test_client_can_fetch_active_restores(self):
        restores = list(self.client.active_restores)
        self.assertGreaterEqual(len(restores), 0)
        for restore in restores:
            self.assertEqual(restore.type, 'Restore')

    def test_client_busy_returns_true_or_false(self):
        self.assertIn(self.client.busy, [True, False])
