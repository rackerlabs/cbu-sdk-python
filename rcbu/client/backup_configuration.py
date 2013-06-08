import os
import json

import requests

from rcbu.common.exceptions import (
    InconsistentInclusionsError, DisconnectedError
)


def _parse_paths(paths):
    return {p['FilePath'] for p in paths}


def _path_type(path):
    return 'Folder' if os.path.isdir(path) else 'File'


def _paths_to_json(paths):
    return [{'FilePath': p,
             'FileItemType': _path_type(p)}
            for p in paths]


def _args_from_dict(resp):
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
        '_inclusions': _parse_paths(resp['Inclusions']),
        '_exclusions': _parse_paths(resp['Exclusions'])
    }
    return args


def _raise_if_not_set_difference_empty(lhs, rhs):
    diff = lhs & rhs
    if len(diff) > 0:
        raise InconsistentInclusionsError(diff)


def from_dict(resp, connection=None):
    args = _args_from_dict(resp)
    return BackupConfiguration(resp.get('BackupConfigurationId', 0),
                               connection,
                               **args)


def from_file(path, connection=None):
    data = None
    with open(path, 'rt') as f:
        data = json.load(f)
    return from_dict(data, connection)


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
        'Inclusions': _paths_to_json(config._inclusions),
        'Exclusions': _paths_to_json(config._exclusions)
    }
    return json.dumps(resp)


class BackupConfiguration(object):
    def __init__(self, config_id, connection=None, **kwargs):
        self._config_id = config_id
        self._inclusions = set()
        self._exclusions = set()
        [setattr(self, k, v) for k, v in kwargs.items()]
        self._connection = connection

    def __repr__(self):
        form = ('<BackupConfiguration id:{0} name:{1} agent:{2} '
                'encrypted:{3} enabled:{4} '
                '#inclusions:{5} #exclusions:{6}>')
        return form.format(self.id, self.name, self.agent_id,
                           self.encrypted, self.enabled,
                           len(self.inclusions),
                           len(self.exclusions))

    @property
    def id(self):
        return getattr(self, "_config_id", None)

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
            raise DisconnectedError()

    def _toggle(self, enabled=None):
        self._check_connection()
        url = '{0}/{1}/{2}/{3}'.format(self._connection.host,
                                       'backup-configuration',
                                       'enable', self.id)
        msg = json.dumps({'Enable': True if enabled else False})
        resp = self._connection.request(requests.post, url, data=msg)
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
                                   self.id)
        self._connection.request(requests.delete, url)

    @property
    def schedule(self):
        return self._schedule

    def reschedule(self, schedule):
        self._schedule.update({
            'frequency': schedule.frequency,
            'start_time': {
                'hour': schedule.hour,
                'minute': schedule.minute,
                'am_or_pm?': schedule.period
            },
            'hourly_interval': schedule.interval,
            'day_of_week': schedule.day_of_week
        })

    @property
    def inclusions(self):
        return self._inclusions

    def include(self, paths):
        """Updates the inclusions for this backup configuration.

        paths: a sequence of paths on the local filesystem.
        """
        self._set_paths(paths, are_exclusions=False)

    @property
    def exclusions(self):
        return self._exclusions

    def exclude(self, paths):
        """Updates the exclusions for this backup configuration.

        paths: a sequence of paths on the local filesystem.
        """
        self._set_paths(paths, are_exclusions=True)

    def _set_paths(self, paths, are_exclusions=False):
        data = {os.path.realpath(p) for p in paths}

        # prevent inconsistent state by checking inclusions
        # and exclusions don't contain common items
        if are_exclusions:
            _raise_if_not_set_difference_empty(self._inclusions, data)
            self._exclusions = data
        else:
            _raise_if_not_set_difference_empty(self._exclusions, data)
            self._inclusions = data

    def reload(self):
        """Captures the latest state from the API."""
        self._check_connection()
        url = '{0}/{1}/{2}'.format(self._connection.host,
                                   'backup-configuration',
                                   self.id)
        resp = self._connection.request(requests.get, url)
        parsed = resp.json()
        args = _args_from_dict(parsed)
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
                                       self.id)
            method = requests.put

        data = to_json(self)
        resp = self._connection.request(method, url, data=data)
        return resp.json() if creating else None

    def create(self):
        """Takes the values stored locally and creates a new configuration.

        The configuration ID of this instance is updated to reflect the
        new configuration that was created.
        """
        resp = self._create_or_update(creating=True)
        self._config_id = resp['BackupConfigurationId']

    def update(self):
        """Takes the local values and updates the remote config."""
        return self._create_or_update(creating=False)
