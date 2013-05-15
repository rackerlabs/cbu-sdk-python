class Connection(object):
    def __init__(self, username, apikey):
        pass

    @property
    def agents():
        pass

    @property
    def backup_configurations():
        pass

    @property
    def restore_configurations():
        pass

    @property
    def api_host():
        pass

    @property
    def api_version():
        pass

    @property
    def active_backups():
        pass

    @property
    def active_restores():
        pass

    def get_agent(agent_id):
        pass

    def get_backup_configuration(config_id):
        pass

    def get_backup_report(backup_id):
        pass

    def create_backup(config_id):
        pass

    def create_restore(config_id):
        pass
