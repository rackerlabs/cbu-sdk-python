import json
import time

import requests

from rcbu.utils.perf import Timer
import rcbu.client.backup_report as backup_report
import rcbu.client.restore_report as restore_report
import rcbu.common.status as status


class Command(object):
    def __init__(self, command_id, command_type, connection, **kwargs):
        self._id = command_id
        self._type = command_type
        self._connection = connection
        [setattr(self, k, v) for k, v in kwargs.items()]

    @property
    def running(self):
        return self.state in status.BUSY_STATUS

    def _fetch_state(self, reload=False):
        if reload:
            self._state = status.Status(self.id, self._type,
                                        self._connection).state
        return self.state

    @property
    def state(self):
        return getattr(self, '_state', 'Unknown')

    @property
    def id(self):
        return self._id

    def connect(self, connection):
        self._connection = connection

    def _action_data(self, starting):
        action = 'StartManual' if starting else 'StopManual'
        data_dict = {'Action': action, 'Id': self._action_id(starting)}
        if getattr(self, "._encrypted", None) and self._type == 'restore':
            data_dict['EncryptedPassword'] = self._encrypted_password
        return json.dumps(data_dict)

    def _action_id(self, starting):
        if starting:
            return self._config_id if self._type == 'backup' else self.id
        else:
            return self.id

    def _action(self, starting):
        url = '{0}/{1}/{2}'.format(self._connection.host, self._type,
                                   'action-requested')
        data = self._action_data(starting)
        resp = self._connection.request(requests.post, url, data=data)
        self._state = 'Preparing' if starting else 'Stopped'
        return resp

    def start(self):
        resp = self._action(starting=True)
        if self._type == 'backup':
            self._id = int(resp.json())
        return resp

    def stop(self):
        return self._action(starting=False)

    def _report(self, body):
        return {
            'backup': lambda body: backup_report.from_dict(self.id, body),
            'restore': lambda body: restore_report.from_dict(self.id, body)
        }[self._type](body)

    @property
    def report(self):
        url = '{0}/{1}/{2}/{3}'.format(self._connection.host,
                                       self._type, 'report', self.id)
        resp = self._connection.request(requests.get, url)
        return self._report(resp.json())

    def _is_done(self):
        state = self._fetch_state(reload=True)
        return state in status.DONE_STATUS

    def wait_for_completion(self, poll_interval=60, timeout=None):
        time_waited = 0
        while not self._is_done():
            with Timer() as start:
                time.sleep(poll_interval)
            time_waited += start.elapsed
            if timeout and time_waited > timeout:
                raise RuntimeError('{} took too long.'.format(self._type))
