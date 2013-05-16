from rcbu.common.show import Show


class Configuration(object, Show):
    def __init__(self, config_id):
        self.config_id = config_id

    def __str__(self):
        return '{}:{}'.format('Configuration', self.config_id)

    @property
    def schedule(self):
        pass

    @property
    def id(self):
        return self.config_id

    @property
    def notification_email(self):
        pass

    def next_runtime(self):
        pass

    def is_enabled(self):
        pass

    def notifies_on_failure(self):
        pass

    def notifies_on_success(self):
        pass

    def update_from_file(self, path):
        pass

    def update_from_dict(self, conf):
        pass

    def disable(self):
        pass

    def enable(self):
        pass

    def delete(self):
        pass
