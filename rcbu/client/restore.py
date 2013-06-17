import json
import requests

from rcbu.client.command import Command


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
    def __init__(self, restore_id, connection, **kwargs):
        Command.__init__(self, restore_id, 'restore', connection, **kwargs)

    def __repr__(self):
        form = ('<Restore id:{0} state:{1} running:{2}>')
        return form.format(self.id, self.state, self.running)

    def _action(self, starting):
        url = '{0}/restore/action-requested'.format(self._connection.host)
        action = 'StartManual' if starting else 'StopManual'
        data = {'Action': action, 'Id': self.id}
        if getattr(self, '_encrypted', None):
            data['EncryptedPassword'] = self._encrypted_password
        resp = self._connection.request(requests.post, url,
                                        data=json.dumps(data))
        self._state = 'Preparing' if starting else 'Stopped'
        return resp

    def start(self):
        return self._action(starting=True)

    def stop(self):
        return self._action(starting=False)
