import json

import requests

from rcbu.client.configuration import Configuration
from rcbu.common.exceptions import InvalidObject


class BackupConfiguration(Configuration):
    def __init__(self, config_id, connection):
        super(BackupConfiguration, self).__init__(config_id)

    @property
    def id(self):
        return self.config_id

    @property
    def agent_id(self):
        return self.agent_id

    @property
    def notification_settings(self):
        pass

    @property
    def name(self):
        return '{0} ({1})'.format(self.name, self.flavor)

    @property
    def encrypted(self):
        """Returns whether this backup is encrypted. Encryption can
        be enabled at the agent level."""
        return self.encrypted

    @property
    def enabled(self):
        return self.enabled

    def _toggle(self, enabled=None):
        url = '{}/{}/{}/{}'.format(self.connection.host,
                                   'backup-configuration',
                                   'enable', self.config_id)
        token = self.connection.token
        hdrs = {'x-auth-token': token, 'content-type': 'application/json'}
        msg = json.dumps({'Enable': True if enabled else False})
        resp = requests.post(url, headers=hdrs, data=msg)
        resp.raise_for_status()
        assert resp.json()['IsActive'] == enabled

    def disable(self):
        self._toggle(False)
        pass

    def enable(self):
        self._toggle(True)
        pass

    @property
    def deleted(self):
        return self.deleted

    def delete(self):
        url = '{}/{}/{}'.format(self.connection.host, 'backup-configuration',
                                self.config_id)
        token = self.connection.token
        resp = requests.delete(url, headers={'x-auth-token': token})
        resp.raise_for_status()
        self.valid = False

    @property
    def schedule(self):
        return '{0}:{1} {2} {3} ({4})'.format(
            self.hour, self.minute, self.ampm, self.day_of_week,
            self.frequency)

    @property
    def inclusions(self):
        return self.inclusions

    def set_inclusions(self, paths):
        pass

    @property
    def exclusions(self):
        return self.exclusions

    def set_exclusions(self, paths):
        pass

    def reload(self):
        """Captures the latest state from the API."""
        pass

    def create(self):
        """Takes the values stored locally and creates a new configuration."""
        pass

    def update(self):
        """Takes the local values and updates the remote config."""
        pass
