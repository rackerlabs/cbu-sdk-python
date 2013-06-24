import datetime

import rcbu.common.exceptions as exceptions


def _args_from_dict(body):
    return {
        '_config_id': body['BackupConfigurationId'],
        '_config_name': body['BackupConfigurationName'],
        '_state': body['State'],
        '_time': {
            'start': body['StartTime'],
            'end': body['CompletedTime'],
            'duration': body['Duration']
        },
        '_num_errors': body['NumErrors'],
        '_outcome': body['Reason'],
        '_diagnostics': body['Diagnostics'],
        '_errors': body['ErrorList']
    }


_error_class = {
    'backup': exceptions.BackupFailed,
    'restore': exceptions.RestoreFailed
}


class Report(object):
    def __init__(self, report_id, report_type, **kwargs):
        self.report_id = report_id
        self._type = report_type
        [setattr(self, k, v) for k, v in kwargs.items()]

    @property
    def id(self):
        return self.report_id

    @property
    def state(self):
        return self._state

    @property
    def errors(self):
        return self._errors

    @property
    def outcome(self):
        return self._outcome

    @property
    def ok(self):
        return len(self.errors) == 0

    @property
    def diagnostics(self):
        return self._diagnostics

    def _parse_date(self, variant):
        timestamp = int(self._time[variant][6:16])
        return datetime.datetime.fromtimestamp(timestamp)

    @property
    def started(self):
        return self._parse_date('start')

    @property
    def ended(self):
        return self._parse_date('start')

    @property
    def duration(self):
        return self._time['duration']

    def raise_if_not_ok(self):
        if not self.ok:
            raise _error_class[self._type](self)
