import datetime
import unittest

import pytz

from rcbu.client.connection import Connection
from tests.utils.credentials import Credentials


class TestConnect(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.creds = Credentials()
        cls.connection = Connection(cls.creds.name, cls.creds.region,
                                    apikey=cls.creds.key)

    def setup(self):
        self.connection = TestConnect.connection

    def test_token_makes_sense(self):
        self.assertEqual(len(self.connection.token), 32)

    def test_tenant_correct(self):
        self.assertEqual(self.connection.tenant, TestConnect.creds.tenant)

    def test_host_correct(self):
        self.assertIn('backup.api.rackspacecloud.com',
                      self.connection.host,)

    def test_api_version_correct(self):
        self.assertEqual(self.connection.api_version, '1.0')
        self.assertEqual(self.connection.api_version_tuple, (1, 0))

    def test_username_correct(self):
        self.assertEqual(self.connection.username, TestConnect.creds.name)

    def test_expires_makes_sense(self):
        self.assertGreater(self.connection.expires,
                           datetime.datetime.now(pytz.utc))
