import json
import time

import requests

from rcbu.client.command import Command
from rcbu.utils.perf import Timer
import rcbu.client.backup_report as backup_report
import rcbu.common.status as status


def _args_from_dict(body):
    return {
        '_config_id': body['BackupConfigurationId'],
        '_state': body['CurrentState'],
        '_agent_id': body['MachineAgentId'],
        '_machine_name': body['MachineName'],
        '_key': {
            'modulus_hex': body['EncryptionKey']['ModulusHex'],
            'exponent_hex': body['EncryptionKey']['ExponentHex']
        }
    }


def from_dict(body):
    return Backup(body['BackupId'], _args_from_dict(body))


class Backup(Command):
    def __init__(self, config, connection=None, **kwargs):
        self._config_id = config.id
        self._connection = connection
        [setattr(self, k, v) for k, v in kwargs.items()]

    @property
    def running(self):
        return self._state in status.BUSY_STATUS

    def _fetch_state(self, reload=False):
        if reload:
            self._state = status.Status(self.id, 'backup',
                                        self._connection).state
        return self._state

    @property
    def state(self):
        return self._state

    @property
    def id(self):
        return getattr(self, '_backup_id', 0)

    def connect(self, connection):
        self._connection = connection

    def _action(self, starting=True):
        action = 'StartManual' if starting else 'StopManual'
        op_id = self._config_id if starting else self.backup_id
        url = '{0}/{1}/{2}'.format(self._connection.host, 'backup',
                                   'action-requested')
        headers = {'X-Auth-Token': self._connection.token,
                   'content-type': 'application/json'}
        data = json.dumps({'Action': action, 'Id': op_id})
        resp = requests.post(url, headers=headers, data=data, verify=False)
        resp.raise_for_status()
        self._state = 'Preparing' if starting else 'Stopped'
        return resp

    def start(self):
        resp = self._action(starting=True)
        self._backup_id = int(resp.content)
        return Status(self._backup_id, self._connection)

    def stop(self):
        return self._action(starting=False)

    @property
    def report(self):
        url = '{0}/{1}/{2}/{3}'.format(self._connection.host,
                                       'backup', 'report', self.id)
        headers = {'x-auth-token': self._connection.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        parsed = resp.json()
        return backup_report.from_dict(parsed['BackupId'], parsed)

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
                raise RuntimeError('Backup took too long.')
