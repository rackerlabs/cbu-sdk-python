import binascii
import json
import os

from rcbu.common.http import Http
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

from rcbu.common.activity_mixin import ExposesActivities
import rcbu.client.backup_configuration as backup_config
from rcbu.utils.bytes import dehumanize_bytes


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
        '_enabled': not body['IsDisabled'],
        '_online': body['Status']
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


class Agent(ExposesActivities):
    def __init__(self, agent_id, connection=None, **kwargs):
        self._agent_id = agent_id
        self._connection = connection
        ExposesActivities.__init__(self, connection, agent_id)
        [setattr(self, k, v) for k, v in kwargs.items()]

    def __repr__(self):
        form = ('<Agent id:{0} name:{1} os:{2}, version:{3} '
                'data_center:{4} encrypted:{5} enabled:{6}>')
        return form.format(self.id, self.name, self.os, self.version,
                           self.data_center, self.encrypted, self.enabled)

    def connect(self, connection):
        self._connection = connection

    @property
    def id(self):
        return self._agent_id

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

    def _fetch_property(self, name):
        url = '{0}/agent/{1}'.format(self._connection.host, self.id)
        resp = self._connection.request(Http.get, url)
        return resp.json()[name]

    @property
    def vault_size(self):
        if self._vault_size is None:
            self._vault_size = self._fetch_property('BackupVaultSize')
        return dehumanize_bytes(self._vault_size)

    @property
    def backup_configurations(self):
        url = '{0}/{1}/{2}/{3}'.format(self._connection.host,
                                       'backup-configuration', 'system',
                                       self.id)
        resp = self._connection.request(Http.get, url)
        return (backup_config.from_dict(b, self._connection)
                for b in resp.json())

    @property
    def online(self):
        '''Lazily-loaded property. Queries the API if the status is unknown.
        Otherwise, it returns the last known state.'''
        if self._online == 'Unknown':
            self._online = self._fetch_property('Status')
        return self._online == 'Online'

    @property
    def encrypted(self):
        return self._encrypted

    def _public_key_path(self):
        name = 'public-key.pem'
        if os.name != 'nt':
            return os.path.join('/etc/driveclient', name)
        else:
            return os.path.join(os.path.expandvars('%appdata%'),
                                'Local', 'Driveclient', name)

    def encrypt(self, password):
        public_key_path = self._public_key_path()
        public_key = None
        with open(public_key_path) as f:
            public_key = f.read()

        pkey = RSA.importKey(public_key)
        cipher = PKCS1_v1_5.new(pkey)
        encrypted_password = cipher.encrypt(password)
        hex_pass = binascii.hexlify(encrypted_password).decode()
        url = '{0}/{1}/{2}'.format(self._connection.host, 'agent', 'encrypt')
        data = json.dumps({
            'MachineAgentId': self.id,
            'EncryptedPasswordHex': hex_pass,
        })
        self._connection.request(Http.post, url, data=data)
        self._encrypted = True

    @property
    def enabled(self):
        return self._enabled

    def _toggle(self, enabled=True):
        url = '{0}/{1}/{2}'.format(self._connection.host, 'agent', 'enable')
        data = json.dumps({
            'MachineAgentId': self.id,
            'Enable': enabled
        })
        self._connection.request(Http.post, url, data=data)
        self._enabled = enabled

    def enable(self):
        self._toggle(enabled=True)

    def disable(self):
        self._toggle(enabled=False)

    def delete(self):
        url = '{0}/{1}/{2}'.format(self._connection.host, 'agent', 'delete')
        data = json.dumps({'MachineAgentId': self.id})
        self._connection.request(Http.post, url, data=data)
