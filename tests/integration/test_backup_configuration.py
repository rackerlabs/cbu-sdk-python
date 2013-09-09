from __future__ import print_function
import os
import shutil
import unittest

import requests

from rcbu.client.connection import Connection
from rcbu.client.client import Client
import rcbu.common.schedule as schedule
import rcbu.client.backup_configuration as backup_config
import tests.mock.configuration as mock_config
from tests.utils.credentials import Credentials
from tests.utils.agent import Agent


class TestBackupConfiguration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.creds = Credentials()
        cls.connection = Connection(cls.creds.name, apikey=cls.creds.key)
        cls.email = cls.creds.email
        cls.agent = Agent()
        os.mkdir('a')

    def setUp(self):
        self.connection = TestBackupConfiguration.connection
        self.client = Client(self.connection)
        self.email = TestBackupConfiguration.email
        self.agent = TestBackupConfiguration.agent
        config = mock_config.backup_configuration(
            name='integration', email=self.email,
            agent_id=self.agent.id
        )
        self.backup_config = backup_config.from_dict(config, self.connection)
        self.backup_config.include(['a'])
        self.backup_config.create()

    def test_fetching_works(self):
        bconf = self.backup_config
        self.assertEqual(bconf.name, 'integration')
        self.assertEqual(bconf.agent_id, 187801)
        self.assertEqual(bconf.email, 'cpp.cabrera@gmail.com')
        self.assertEqual(bconf.notify_on_success, False)
        self.assertEqual(bconf.notify_on_failure, True)
        self.assertEqual(bconf.encrypted, False)
        self.assertEqual(bconf.enabled, True)
        self.assertEqual(bconf.deleted, False)
        self.assertEqual(bconf.schedule, schedule.manually())
        self.assertEqual(bconf.inclusions, set([os.path.realpath('a')]))
        self.assertEqual(bconf.exclusions, set())

    def test_can_rename(self):
        old_name = self.backup_config.name
        self.backup_config.rename('taco')
        self.assertIsNone(self.backup_config.update())
        self.backup_config.reload()
        self.assertNotEqual(old_name, self.backup_config.name)
        self.assertEqual(self.backup_config.name, 'taco')

    def test_can_disable_then_re_enable(self):
        self.assertEqual(self.backup_config.enabled, True)
        self.backup_config.disable()
        self.assertEqual(self.backup_config.enabled, False)
        self.backup_config.enable()
        self.assertEqual(self.backup_config.enabled, True)

    def _reschedule_test(self, xschedule):
        self.backup_config.reschedule(xschedule)
        self.backup_config.update()
        self.assertEqual(self.backup_config.schedule, xschedule)

    def test_can_reschedule_to_daily(self):
        self._reschedule_test(schedule.daily(hour=1, minute=1))

    def test_can_reschedule_to_hourly(self):
        self._reschedule_test(schedule.hourly(interval=4))

    def test_can_reschedule_to_weekly(self):
        self._reschedule_test(schedule.weekly(0, hour=1, minute=1))

    def test_can_add_inclusions(self):
        os.mkdir('b')
        self.backup_config.include(['b'])
        self.backup_config.update()
        self.assertEqual(self.backup_config.inclusions,
                         {os.path.realpath(p) for p in ['a', 'b']})
        shutil.rmtree('b')

    def test_can_add_exclusions(self):
        os.mkdir('b')
        excl_paths = [os.path.join('b', str(i)) for i in range(10)]
        for p in excl_paths:
            with open(p, 'wb') as f:
                f.write(b'1')
        self.backup_config.include(['b'])
        self.backup_config.exclude(excl_paths)
        self.backup_config.update()
        self.assertEqual(self.backup_config.inclusions,
                         {os.path.realpath(p) for p in ['a', 'b']})
        self.assertEqual(self.backup_config.exclusions,
                         {os.path.realpath(p) for p in excl_paths})
        shutil.rmtree('b')

    def test_delete_works(self):
        config = mock_config.backup_configuration(
            name='deleter', email=self.email,
            agent_id=self.agent.id
        )
        conf = backup_config.from_dict(config, self.connection)
        conf.include(['a'])
        conf.create()
        conf.delete()
        with self.assertRaises(requests.exceptions.HTTPError):
            conf.reload()
        self.assertEqual(conf.deleted, True)

    def tearDown(self):
        self.backup_config.delete()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree('a')
