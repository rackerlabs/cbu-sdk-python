import json
import unittest

from httpretty import HTTPretty, httprettified, Response

from rcbu.common.auth import IDENTITY_TOKEN_URL
from rcbu.client.connection import Connection
from rcbu.utils.perf import Timer
import tests.mock.auth as mock_auth
import tests.mock.report as mock_report
import rcbu.client.command as command


def _mock_auth(status):
    reply = mock_auth.authenticate()
    HTTPretty.register_uri(HTTPretty.POST, IDENTITY_TOKEN_URL,
                           status=status, body=json.dumps(reply))


def _mock_status(status_id, status):
    return {
        'RestoreStateId': status_id,
        'CurrentState': status
    }


def _mock_status_done():
    return _mock_status(3, 'Completed')


def _mock_status_working():
    return _mock_status(2, 'InProgress')


class TestCommand(unittest.TestCase):
    @httprettified
    def setUp(self):
        _mock_auth(200)
        self.connection = Connection('a', 'b')
        self.cmd = command.Command(1, 'backup', self.connection)

    def test_default_state_matches_expected(self):
        self.assertEqual(self.cmd.state, 'Unknown')

    def test_id_matches_expected(self):
        self.assertEqual(self.cmd.id, 1)

    def test_connect_works(self):
        self.cmd.connect(None)
        self.assertEqual(self.cmd._connection, None)

    def test_running_matches_expected(self):
        self.assertEqual(self.cmd.running, False)

    @httprettified
    def test_get_report_works(self):
        url = '{0}/{1}/report/{2}'.format(self.connection.host, self.cmd._type,
                                          self.cmd.id)
        mock = mock_report.backup_report()
        HTTPretty.register_uri(HTTPretty.GET, url, body=json.dumps(mock))
        report = self.cmd.report
        self.assertEqual(report.id, 1)
        self.assertTrue(report.ok)

    @httprettified
    def test_wait_for_completion_throws_on_timeout(self):
        url = '{0}/{1}/{2}'.format(self.connection.host, self.cmd._type,
                                   self.cmd.id)
        HTTPretty.register_uri(HTTPretty.GET, url,
                               body=json.dumps(_mock_status_working()))
        with self.assertRaises(RuntimeError):
            self.cmd.wait_for_completion(poll_interval=.005, timeout=.0025)

    @httprettified
    def test_wait_for_completion_works_poll_none(self):
        url = '{0}/{1}/{2}'.format(self.connection.host, self.cmd._type,
                                   self.cmd.id)
        HTTPretty.register_uri(HTTPretty.GET, url,
                               body=json.dumps(_mock_status_done()))
        with Timer() as timed:
            self.cmd.wait_for_completion(poll_interval=.005)
        self.assertLess(timed.elapsed, .005)

    @httprettified
    def test_wait_for_completion_works_poll_once(self):
        url = '{0}/{1}/{2}'.format(self.connection.host, self.cmd._type,
                                   self.cmd.id)
        resps = [
            Response(body=json.dumps(_mock_status_working())),
            Response(body=json.dumps(_mock_status_done()))
        ]
        HTTPretty.register_uri(HTTPretty.GET, url, responses=resps)
        with Timer() as timed:
            self.cmd.wait_for_completion(poll_interval=.005)
        self.assertGreater(timed.elapsed, .005)
        self.assertLess(timed.elapsed, .015)
