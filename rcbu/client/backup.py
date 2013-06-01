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


def from_dict(body):
    return Backup(body['BackupId'], _args_from_dict(body))


class Backup(Command):
    def __init__(self, config, connection, **kwargs):
        self._config_id = config.id
        Command.__init__(self, 0, 'backup', connection, **kwargs)
