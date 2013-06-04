from rcbu.client.command import Command


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
