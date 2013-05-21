import os
import json

import requests

from rcbu.client.configuration import Configuration


def _args_from_json(resp):
    """Returns a {} appropriate for constructing a BackupConfiguration."""
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
                'am_or_pm?': resp['StartTimeAmPm']
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
    return args


def from_json(resp):
    args = _args_from_json(resp)
    return BackupConfiguration(resp['BackupConfigurationId'], **args)


def from_file(path):
    data = None
    with open(path, 'rt') as f:
        data = json.load(f)
    return from_json(data)


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
        'StartTimeAmPm': start_time['am_or_pm?'],
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

    def update_notification_settings(self, email, notify_on_failure=True,
                                     notify_on_success=False):
        self._notify['email'] = email
        self._notify['on_failure'] = notify_on_failure
        self._notify['on_success'] = notify_on_success

    @property
    def name(self):
        return self._name

    def change_name(self, name):
        self._name = name

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
        url = '{0}/{1}/{2}/{3}'.format(self._connection.host,
                                       'backup-configuration',
                                       'enable', self.config_id)
        token = self._connection.token
        hdrs = {'x-auth-token': token, 'content-type': 'application/json'}
        msg = json.dumps({'Enable': True if enabled else False})
        resp = requests.post(url, headers=hdrs, data=msg, verify=False)
        resp.raise_for_status()
        assert resp.json()['IsActive'] == enabled
        self._enabled = enabled

    def disable(self):
        self._toggle(False)

    def enable(self):
        self._toggle(True)

    @property
    def deleted(self):
        return self._deleted

    def delete(self):
        self._check_connection()
        url = '{0}/{1}/{2}'.format(self._connection.host,
                                   'backup-configuration',
                                   self.config_id)
        token = self._connection.token
        resp = requests.delete(url, headers={'x-auth-token': token},
                               verify=False)
        resp.raise_for_status()

    @property
    def schedule(self):
        return self._schedule

    @property
    def inclusions(self):
        return self._inclusions

    def set_inclusions(self, paths):
        """Updates the inclusions for this backup configuration.

        paths: a [] of paths on the local filesystem.
        """
        self._set_paths(paths, are_exclusions=False)

    @property
    def exclusions(self):
        return self._exclusions

    def set_exclusions(self, paths):
        """Updates the exclusions for this backup configuration.

        paths: a [] of paths on the local filesystem.
        """
        self._set_paths(paths, are_exclusions=True)

    def _set_paths(self, paths, are_exclusions=False):
        data = [
            {"FileItemType": ("Folder" if os.path.isdir(p) else "File"),
             "FilePath": os.path.realpath(p)} for p in paths]
        if are_exclusions:
            self._exclusions = data
        else:
            self._inclusions = data

    def reload(self):
        """Captures the latest state from the API."""
        self._check_connection()
        url = '{0}/{1}/{2}'.format(self._connection.host,
                                   'backup-configuration',
                                   self.id)
        headers = {'x-auth-token': self._connection.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status
        parsed = resp.json()
        args = _args_from_json(parsed)
        [setattr(self, k, v) for k, v in args.items()]

    def _create_or_update(self, creating=False):
        self._check_connection()
        url = None
        method = None

        if creating:
            url = '{0}/{1}'.format(self._connection.host,
                                   'backup-configuration')
            method = requests.post
        else:
            url = '{0}/{1}/{2}'.format(self._connection.host,
                                       'backup-configuration',
                                       self.config_id)
            method = requests.put

        data = to_json(self)
        headers = {
            'x-auth-token': self._connection.token,
            'content-type': 'application/json'
        }
        resp = method(url, headers=headers, data=data, verify=False)
        resp.raise_for_status()
        print(resp, resp.content)
        return resp.json() if creating else None

    def create(self):
        """Takes the values stored locally and creates a new configuration.

        The configuration ID of this instance is updated to reflect the
        new configuration that was created.
        """
        self._check_connection()
        resp = self._create_or_update(creating=True)
        self.config_id = resp['BackupConfigurationId']

    def update(self):
        """Takes the local values and updates the remote config."""
        self._check_connection()
        return self._create_or_update(creating=False)
