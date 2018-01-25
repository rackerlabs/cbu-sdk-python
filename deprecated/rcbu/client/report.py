import rcbu.common.exceptions as exceptions
import rcbu.common.duration as duration
import rcbu.utils.date as date


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

    @property
    def started(self):
        return date.parse(self._time['start'])

    @property
    def ended(self):
        return date.parse(self._time['end'])

    @property
    def duration(self):
        return duration.seconds(self._time['duration'])

    def raise_if_not_ok(self):
        if not self.ok:
            raise _error_class[self._type](self)
