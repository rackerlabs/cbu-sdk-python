import json
import time

import requests

from rcbu.client.command import Command
from rcbu.utils.perf import Timer
import rcbu.common.status as status
import rcbu.client.restore_report as restore_report


def _args_from_dict(body):
    return {
        '_backup_id': body['BackupId'],
        '_overwrite': body['OverwriteFiles'],
        '_backup_config_id': body['BackupConfigurationId'],
        '_backup_config_name': body['BackupConfigurationName'],
        '_source_machine_id': body['BackupMachineId'],
        '_source_machine_name': body['BackupMachineName'],
        '_destination_agent_id': body['DestinationMachineId'],
        '_destination_machine_name': body['DestinationMachineName'],
        '_destination_path': body['DestinationPath'],
        '_encrypted': body['IsEncrypted'],
        '_encrypted_password': body['EncryptedPassword'],
        '_key': {
            'modulus': body['PublicKey']['ModulusHex'],
            'exponent': body['PublicKey']['ExponentHex']
        }
    }


def from_dict(body, connection=None):
    args = _args_from_dict(body)
    return Restore(body['RestoreId'], connection=connection, **args)


def from_file(path, connection=None):
    data = None
    with open(path, 'rt') as f:
        data = json.load(f)
    return from_dict(data, connection)


class Restore(Command):
    def __init__(self, restore_id, connection=None, **kwargs):
        self._id = restore_id
        self._connection = connection
        [setattr(self, k, v) for k, v in kwargs.items()]

    @property
    def running(self):
        return self._state in status.BUSY_STATUS

    def _fetch_state(self, reload=False):
        if reload:
            self._state = status.Status(self.id, 'restore',
                                        self._connection).state
        return self._state

    @property
    def state(self):
        return self._state

    @property
    def id(self):
        return self._id

    def connect(self, connection):
        self._connection = connection

    def _action(self, starting=True):
        action = 'StartManual' if starting else 'StopManual'
        url = '{0}/{1}/{2}'.format(self._connection.host, 'restore',
                                   'action-requested')
        headers = {'X-Auth-Token': self._connection.token,
                   'content-type': 'application/json'}

        data_dict = {'Action': action, 'Id': self.id}
        if self._encrypted:
            data_dict['EncryptedPassword'] = self._encrypted_password
        data = json.dumps(data_dict)
        resp = requests.post(url, headers=headers, data=data, verify=False)
        resp.raise_for_status()
        self._state = 'Preparing' if starting else 'Stopped'
        return resp

    def start(self):
        return self._action(starting=True)

    def stop(self):
        return self._action(starting=False)

    @property
    def report(self):
        url = '{0}/{1}/{2}/{3}'.format(self._connection.host,
                                       'restore', 'report', self.id)
        headers = {'x-auth-token': self._connection.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return restore_report.from_dict(self.id, resp.json())

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
