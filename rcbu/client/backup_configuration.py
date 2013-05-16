from rcbu.client.configuration import Configuration


class BackupConfiguration(Configuration):
    def __init__(self, config_id,
                 agent_id=None, config_name=None, active=None,
                 frequency=None, data_rentention_days=None,
                 inclusions=None, exclusions=None):
        self.config_id = config_id
        self.agent_id = agent_id
        self.active = active
        self.frequency = frequency
        self.data_retention_days = data_rentention_days
        self.inclusions = inclusions
        self.exclusions = exclusions
