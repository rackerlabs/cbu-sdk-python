import json

import requests

from rcbu.client.configuration import Configuration
from rcbu.common.exceptions import InvalidObject


class BackupConfiguration(Configuration):
    def __init__(self, config_id, connection,
                 agent_id=None, config_name=None, active=None,
                 frequency=None, data_rentention_days=None,
                 inclusions=None, exclusions=None,
                 email=None, enabled=None, next_runtime=None,
                 last_runtime=None, last_backup_id=None,
                 notify_on_fail=None, notify_on_success=None):
        super(BackupConfiguration, self).__init__(config_id)
        self.agent_id = agent_id
        self.active = active
        self.frequency = frequency
        self.data_retention_days = data_rentention_days
        self.inclusions = inclusions
        self.exclusions = exclusions
        self.email = email
        self.connection = connection
        self.enabled = enabled
        self.notify_on_fail = notify_on_fail
        self.notify_on_success = notify_on_success
        self.runtime = next_runtime
        self.last_runtime = last_runtime
        self.last_backup_id = last_backup_id
        self.valid = True

    def _valid_or_raise(self):
        if not self.valid:
            raise InvalidObject()

    def _get_update(self):
        return self.connection.get_backup_configuration(self.config_id)

    @property
    def id(self):
        self._valid_or_raise()
        return self.config_id

    @property
    def notification_email(self):
        self._valid_or_raise()
        return self.email

    def next_runtime(self):
        return self._get_update().runtime

    def is_enabled(self):
        return self._get_update().enabled

    def notifies_on_failure(self):
        self._valid_or_raise()
        return self.notify_on_fail

    def notifies_on_success(self):
        self._valid_or_raise()
        return self.notify_on_success

    def update_from_file(self, path):
        pass

    def update_from_dict(self, conf):
        pass

    def _toggle(self, enabled=None):
        self._valid_or_raise()
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

    def delete(self):
        self._valid_or_raise()
        url = '{}/{}/{}'.format(self.connection.host, 'backup-configuration',
                                self.config_id)
        token = self.connection.token
        resp = requests.delete(url, headers={'x-auth-token': token})
        resp.raise_for_status()
        self.valid = False
