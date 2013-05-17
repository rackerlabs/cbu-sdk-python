from rcbu.common.show import Show


class Agent(Show):
    def __init__(self, agent_id, connection,
                 version=None, datacenter=None,
                 vault_size=None, host=None,
                 enabled=None, encrypted=None, os=None,
                 machine_name=None):
        self.agent_id = agent_id
        self.version = version
        self.datacenter = datacenter
        self.vault_size = vault_size
        self.host = host
        self.enabled = enabled
        self.encrypted = encrypted
        self.os = os
        self.machine_name = machine_name
        self.connection = connection

    def __str__(self):
        return '{}:{}'.format('Agent', self.agent_id)

    @property
    def name(self):
        return self.machine_name

    @property
    def backup_configurations(self):
        pass

    @property
    def restore_configurations(self):
        pass

    @property
    def active_backups(self):
        pass

    @property
    def active_restores(self):
        pass

    def is_busy(self):
        pass

    def is_encrypted(self):
        pass

    def is_enabled(self):
        pass

    def enable(self):
        pass

    def disable(self):
        pass

    def delete(self):
        pass

    def encrypt(self):
        pass
