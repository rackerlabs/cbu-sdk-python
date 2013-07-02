import json

from rcbu.client.command import Command
from rcbu.common.http import Http


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


def from_dict(body, connection=None):
    return Backup(config_id=body['BackupConfigurationId'],
                  backup_id=body['BackupId'],
                  connection=connection,
                  **_args_from_dict(body))


class Backup(Command):
    def __init__(self, config_id, backup_id=None, connection=None, **kwargs):
        self._config_id = config_id
        Command.__init__(self, backup_id, 'backup', connection, **kwargs)

    def __repr__(self):
        form = ('<Backup id:{0} state:{1} running:{2}>')
        return form.format(self.id, self.state, self.running)

    def _action(self, starting):
        url = '{0}/backup/action-requested'.format(self._connection.host)
        action = 'StartManual' if starting else 'StopManual'
        action_id = self._config_id if starting else self.id
        data = {'Action': action, 'Id': action_id}
        resp = self._connection.request(Http.post, url,
                                        data=json.dumps(data))
        self._state = 'Preparing' if starting else 'Stopped'
        return resp

    def start(self):
        resp = self._action(starting=True)
        self._id = int(resp.json())
        return resp

    def stop(self):
        return self._action(starting=False)
