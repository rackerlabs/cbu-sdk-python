class Agent(object):
    def __init__(self, agent_id):
        self.agent_id = agent_id
        pass

    @property
    def name(self):
        pass

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
