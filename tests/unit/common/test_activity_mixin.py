import json
import unittest

from httpretty import HTTPretty, httprettified

import rcbu.common.activity_mixin as activities
from tests.mock.activity import activity

HOST = 'https://tacobackup.com'
KEY = '1234'
AGENT_ID = 1


class Mock(activities.ExposesActivities):
    def __init__(self, host, key, oid):
        activities.ExposesActivities.__init__(self, host, key, oid)


class TestActivityMixin(unittest.TestCase):
    def setUp(self):
        self.agent = Mock(HOST, KEY, AGENT_ID)
        self.url = '{0}/system/activity/{1}'.format(HOST, AGENT_ID)

    @httprettified
    def _activity_test(self, method, xtype, xstatus, xcount):
        activities = [activity(activity_id=i,
                               type_tag=xtype,
                               state=xstatus)
                      for i in range(xcount)]
        HTTPretty.register_uri(HTTPretty.GET, self.url,
                               body=json.dumps(activities))
        result = getattr(self.agent, method)
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
