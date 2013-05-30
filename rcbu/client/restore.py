import json

from rcbu.client.command import Command
import rcbu.common.jobs as jobs


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
        return self._state in jobs.BUSY_STATUS

    def _fetch_state(self, reload=False):
        if reload:
            self._state = Status(self.id, self._connection).state
        return self._state

    @property
    def state(self):
        return self._state

    @property
    def inclusions(self):
        pass

    @property
    def exclusions(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def report(self):
        pass
