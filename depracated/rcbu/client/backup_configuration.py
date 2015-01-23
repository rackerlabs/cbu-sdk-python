import os
import json

import rcbu.common.schedule as schedule
from rcbu.common.exceptions import (
    InconsistentInclusionsError, DisconnectedError
)
from rcbu.common.http import Http


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
        '_on_missed_backup': resp['MissedBackupActionId'],
        '_time_zone': resp['TimeZoneId'],
        '_schedule': schedule.from_dict(resp),
        '_notify': {
            'email': resp['NotifyRecipients'],
            'on_success': resp['NotifySuccess'],
            'on_failure': resp['NotifyFailure']
        },
        '_inclusions': _parse_paths(resp['Inclusions']),
        '_exclusions': _parse_paths(resp['Exclusions'])
    }
    return args


def _raise_if_overlapping(lhs, rhs):
    diff = lhs & rhs
    if len(diff) > 0:
        raise InconsistentInclusionsError(diff)


def _raise_if_not_exists(path):
    if not os.path.exists(path):
        raise IOError(path)


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
    resp = {
        'MachineAgentId': config.agent_id,
        'BackupConfigurationName': config.name,
        'IsActive': config.enabled,
        'VersionRetention': config._retention,
        'MissedBackupActionId': config._on_missed_backup,
        'TimeZoneId': config._time_zone,
        'NotifyRecipients': config.email,
        'NotifySuccess':  config.notify_on_success,
        'NotifyFailure': config.notify_on_failure,
        'Inclusions': _paths_to_json(config._inclusions),
        'Exclusions': _paths_to_json(config._exclusions)
    }
    resp.update(config.schedule.to_api())
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
    def email(self):
        return self._notify['email']

    @property
    def notify_on_success(self):
        return self._notify['on_success']

    @property
    def notify_on_failure(self):
        return self._notify['on_failure']

    def update_notification_settings(self, email, notify_on_failure=True,
                                     notify_on_success=False):
        self._notify['email'] = email
        self._notify['on_failure'] = notify_on_failure
        self._notify['on_success'] = notify_on_success

    @property
    def name(self):
        return self._name

    def rename(self, name):
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
        resp = self._connection.request(Http.post, url, data=msg)
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
        self._connection.request(Http.delete, url)
        self._deleted = True

    @property
    def schedule(self):
        return self._schedule

    def reschedule(self, schedule):
        self._schedule = schedule

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
        for path in data:
            _raise_if_not_exists(path)

        # prevent inconsistent state by checking inclusions
        # and exclusions don't contain common items
        if are_exclusions:
            _raise_if_overlapping(self._inclusions, data)
            self._exclusions.update(data)
        else:
            _raise_if_overlapping(self._exclusions, data)
            self._inclusions.update(data)

    def reload(self):
        """Captures the latest state from the API."""
        self._check_connection()
        url = '{0}/{1}/{2}'.format(self._connection.host,
                                   'backup-configuration',
                                   self.id)
        resp = self._connection.request(Http.get, url)
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
            method = Http.post
        else:
            url = '{0}/{1}/{2}'.format(self._connection.host,
                                       'backup-configuration',
                                       self.id)
            method = Http.put

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
