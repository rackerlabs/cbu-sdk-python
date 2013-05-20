import os
import json

import requests

from rcbu.client.configuration import Configuration


def from_json(resp):
    args = {
        '_agent_id': resp['MachineAgentId'],
        '_name': resp['BackupConfigurationName'],
        '_enabled': resp['IsActive'],
        '_deleted': resp['IsDeleted'],
        '_encrypted': resp['IsEncrypted'],
        '_retention': resp['VersionRetention'],
        '_schedule': {
            'on_missed_backup': resp['MissedBackupActionId'],
            'frequency': resp['Frequency'],
            'start_time': {
                'hour': resp['StartTimeHour'],
                'minute': resp['StartTimeMinute'],
                'am?': resp['StartTimeAmPm'].lower() == 'am'
            },
            'time_zone': resp['TimeZoneId'],
            'hourly_interval': resp['HourInterval'],
            'day_of_week': resp['DayOfWeekId']
        },
        '_notify': {
            'email': resp['NotifyRecipients'],
            'on_success': resp['NotifySuccess'],
            'on_failure': resp['NotifyFailure']
        },
        '_inclusions': resp['Inclusions'],
        '_exclusions': resp['Exclusions']
    }

    return BackupConfiguration(resp['BackupConfigurationId'], **args)


def to_json(config):
    schedule = config._schedule
    start_time = schedule['start_time']
    notify = config._notify
    resp = {
        'MachineAgentId': config._agent_id,
        'BackupConfigurationName': config._name,
        'IsActive': config._enabled,
        'VersionRetention': config._retention,
        'MissedBackupActionId': schedule['on_missed_backup'],
        'Frequency': schedule['frequency'],
        'StartTimeHour': start_time['hour'],
        'StartTimeMinute': start_time['minute'],
        'StartTimeAmPm': 'Am' if start_time['am?'] else 'Pm',
        'DayOfWeekId': schedule['day_of_week'],
        'HourInterval': schedule['hourly_interval'],
        'TimeZoneId': schedule['time_zone'],
        'NotifyRecipients': notify['email'],
        'NotifySuccess': notify['on_success'],
        'NotifyFailure': notify['on_failure'],
        'Inclusions': config._inclusions,
        'Exclusions': config._exclusions
    }
    return json.dumps(resp)


class DisconnectedError(Exception):
    pass


class BackupConfiguration(Configuration):
    def __init__(self, config_id, **kwargs):
        super(BackupConfiguration, self).__init__(config_id)
        [setattr(self, k, v) for k, v in kwargs.items()]
        self._connection = None

    @property
    def id(self):
        return self.config_id

    @property
    def agent_id(self):
        return self._agent_id

    @property
    def notification_settings(self):
        return self._notify

    @property
    def name(self):
        return self._name

    @property
    def encrypted(self):
        """Returns whether this backup is encrypted. Encryption can
        be enabled at the agent level."""
        return self._encrypted

    @property
    def enabled(self):
        return self._enabled

    def connect(self, connection):
        self._connection = connection

    def _check_connection(self):
        if not self._connection:
            raise DisconnectedError('Must self.connect before attempting.')

    def _toggle(self, enabled=None):
        self._check_connection()
        url = '{}/{}/{}/{}'.format(self._connection.host,
                                   'backup-configuration',
                                   'enable', self.config_id)
        token = self._connection.token
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
        return self._deleted

    def delete(self):
        self._check_connection()
        url = '{}/{}/{}'.format(self._connection.host, 'backup-configuration',
                                self.config_id)
        token = self._connection.token
        resp = requests.delete(url, headers={'x-auth-token': token})
        resp.raise_for_status()
        self.valid = False

    @property
    def schedule(self):
        pass

    @property
    def inclusions(self):
        return self._inclusions

    def set_inclusions(self, paths):
        self._set_paths(paths, are_exclusions=False)

    @property
    def exclusions(self):
        return self._exclusions

    def set_exclusions(self, paths):
        self._set_paths(paths, are_exclusions=True)

    def _set_paths(self, paths, are_exclusions=False):
        data = [
            {"FileItemType": ("Directory" if os.path.isdir(p) else "File"),
             "FilePath": os.path.realpath(p)} for p in paths]
        if are_exclusions:
            self._exclusions = data
        else:
            self._inclusions = data

    def reload(self):
        """Captures the latest state from the API."""
        self._check_connection()
        pass

    def create(self):
        """Takes the values stored locally and creates a new configuration."""
        self._check_connection()
        pass

    def update(self):
        """Takes the local values and updates the remote config."""
        self._check_connection()
        pass
