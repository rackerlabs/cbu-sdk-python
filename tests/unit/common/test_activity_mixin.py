import json
import unittest

from httpretty import HTTPretty, httprettified

import rcbu.common.activity_mixin as activities
from rcbu.client.connection import Connection
from rcbu.common.constants import IDENTITY_TOKEN_URL
from tests.mock.activity import activity
from tests.mock.auth import authenticate

AGENT_ID = 1


class Mock(activities.ExposesActivities):
    def __init__(self, connection, oid):
        activities.ExposesActivities.__init__(self, connection, oid)


class TestActivityMixin(unittest.TestCase):
    @httprettified
    def setUp(self):
        reply = authenticate()
        HTTPretty.register_uri(HTTPretty.POST, IDENTITY_TOKEN_URL,
                               status=200, body=json.dumps(reply))
        self.connection = Connection('a', 'dfw', password='c')
        self.agent = Mock(self.connection, AGENT_ID)
        self.url = '{0}/system/activity/{1}'.format(self.connection.host,
                                                    AGENT_ID)

    @httprettified
    def _activity_test(self, method, xtype, xstatus, xcount):
        activities = [activity(activity_id=i,
                               type_tag=xtype,
                               state=xstatus)
                      for i in range(xcount)]
        HTTPretty.register_uri(HTTPretty.GET, self.url,
                               body=json.dumps(activities))
        result = list(getattr(self.agent, method))
        self.assertEqual(len(result), xcount)
        for a in result:
            self.assertEqual(a.type, xtype)
            self.assertEqual(a.state, xstatus)

    @httprettified
    def _busy_test(self, xbusy, count=5):
        activities = [activity(activity_id=i,
                               type_tag='Restore',
                               state='Completed')
                      for i in range(count)]
        extra_jobs_status = 'Complete' if not xbusy else 'InProgress'
        activities.extend(activity(activity_id=i,
                                   type_tag='Backup',
                                   state=extra_jobs_status)
                          for i in range(count))
        HTTPretty.register_uri(HTTPretty.GET, self.url,
                               body=json.dumps(activities))
        self.assertEqual(self.agent.busy, xbusy)

    def test_backup_history_returns_expected(self):
        self._activity_test('backup_history', 'Backup', 'Completed', 5)

    def test_restore_history_returns_expected(self):
        self._activity_test('restore_history', 'Restore', 'Completed', 5)

    def test_cleanup_history_returns_expected(self):
        self._activity_test('cleanup_history', 'Cleanup', 'Completed', 5)

    def test_active_backups_returns_expected(self):
        self._activity_test('active_backups', 'Backup', 'InProgress', 5)

    def test_active_restores_returns_expected(self):
        self._activity_test('active_restores', 'Restore', 'InProgress', 5)

    def test_active_cleanups_returns_expected(self):
        self._activity_test('active_cleanups', 'Cleanup', 'InProgress', 5)

    def test_active_returns_expected(self):
        self._activity_test('active', 'Cleanup', 'InProgress', 5)

    def test_history_returns_expected(self):
        self._activity_test('history', 'Restore', 'Completed', 5)

    def test_busy_returns_true_when_there_are_running_jobs(self):
        self._busy_test(True)

    def test_busy_returns_false_when_agent_is_idle(self):
        self._busy_test(False)
