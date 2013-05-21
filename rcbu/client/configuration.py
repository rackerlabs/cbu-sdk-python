from rcbu.common.show import Show


class Configuration(Show):
    def __init__(self, config_id):
        self.config_id = config_id

    def __str__(self):
        return '{}:{}'.format('Configuration', self.config_id)

    @property
    def id(self):
        return self.config_id
