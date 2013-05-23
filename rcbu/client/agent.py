import json

import requests

from rcbu.common.show import Show
from rcbu.common.constants import ENCRYPT_KEY_URL
from rcbu.common.jobs import is_running
import rcbu.client.backup_configuration as backup_config


def _args_from_dict(body):
    args = {
        '_version': body['AgentVersion'],
        '_vault_size': body['BackupVaultSize'],
        '_allow_cleanups': body['CleanupAllowed'],
        '_data_center': body['Datacenter'],
        '_ipv4': body['IPAddress'],
        '_machine_name': body['MachineName'],
        '_os': {
            'type': body['OperatingSystem'],
            'version': body['OperatingSystemVersion']
        },
        '_encrypted': body['IsEncrypted'],
        '_enabled': not body['IsDisabled']
    }
    return args


def from_dict(body, connection=None):
    args = _args_from_dict(body)
    return Agent(body.get('MachineAgentId', 0), connection, **args)


def from_file(path, connection=None):
    data = None
    with open(path, 'rt') as f:
        data = json.load(f)
    return from_dict(data, connection)


class Agent(Show):
    def __init__(self, agent_id, connection=None, **kwargs):
        self.agent_id = agent_id
        self._connection = connection
        [setattr(self, k, v) for k, v in kwargs.items()]

    def __str__(self):
        return '{0}:{1}'.format('Agent', self.agent_id)

    def connect(self, connection):
        self._connection = connection

    @property
    def id(self):
        return self.agent_id

    @property
    def version(self):
        return self._version

    @property
    def name(self):
        return self._machine_name

    @property
    def os(self):
        return '{0} {1}'.format(self._os['type'], self._os['version'])

    @property
    def data_center(self):
        return self._data_center

    @property
    def backup_configurations(self):
        url = '{0}/{1}/{2}/{3}'.format(self._connection.host,
                                       'backup-configuration', 'system',
                                       self.id)
        headers = {'x-auth-token': self._connection.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return [backup_config.from_dict(b) for b in resp.json()]

    def _jobs(self, predicate):
        url = '{0}/{1}/{2}/{3}'.format(self._connection.host,
                                       'system', 'activity',
                                       self.id)
        headers = {'x-auth-token': self._connection.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return [j for j in resp.json() if predicate(j)]

    @property
    def backup_history(self):
        return self._jobs(lambda job: job['Type'] == 'Backup' and
                          not is_running(job))

    @property
    def restore_history(self):
        return self._jobs(lambda job: job['Type'] == 'Restore' and
                          not is_running(job))

    @property
    def active_backups(self):
        return self._jobs(lambda job: job['Type'] == 'Backup' and
                          is_running(job))

    @property
    def active_restores(self):
        return self._jobs(lambda job: job['Type'] == 'Restore' and
                          is_running(job))

    @property
    def busy(self):
        return len(self._jobs(lambda job: is_running(job))) > 0

    @property
    def encrypted(self):
        return self._encrypted

    def encrypt(self, encrypted_key_hex):
        if not len(encrypted_key_hex) == 512:
            raise ValueError("key should be 512 bytes long: see "
                             "{} for more details".format(ENCRYPT_KEY_URL))

        url = '{0}/{1}/{2}'.format(self._connection.host, 'agent', 'encrypt')
        headers = {'x-auth-token': self._connection.token,
                   'content-type': 'application/json'}
        data = json.dumps({
            'MachineAgentId': self.id,
            'EncryptedPasswordHex': encrypted_key_hex
        })
        resp = requests.post(url, headers=headers, data=data, verify=False)
        resp.raise_for_status()
        self._encrypted = True

    @property
    def enabled(self):
        return self._enabled

    def _toggle(self, enabled=True):
        url = '{0}/{1}/{2}'.format(self._connection.host, 'agent', 'enable')
        headers = {'x-auth-token': self._connection.token,
                   'content-type': 'application/json'}
        data = json.dumps({
            'MachineAgentId': self.id,
            'Enable': enabled
        })
        resp = requests.post(url, headers=headers, data=data, verify=False)
        resp.raise_for_status()
        self._enabled = enabled

    def enable(self):
        self._toggle(enabled=True)

    def disable(self):
        self._toggle(enabled=False)

    def delete(self):
        url = '{0}/{1}/{2}'.format(self._connection.host, 'agent', 'delete')
        headers = {'x-auth-token': self._connection.token,
                   'content-type': 'application/json'}
        data = json.dumps({'MachineAgentId': self.id})
        resp = requests.post(url, headers=headers, data=data, verify=False)
        resp.raise_for_status()
