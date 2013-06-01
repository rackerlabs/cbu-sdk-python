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


class Report(object):
    def __init__(self, report_id, **kwargs):
        self.report_id = report_id
        [setattr(self, k, v) for k, v in kwargs.items()]

    @property
    def id(self):
        return self._id

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
        return self._time['start']

    @property
    def ended(self):
        return self._time['ended']

    @property
    def duration(self):
        return self._time['duration']

    def raise_if_not_ok(self):
        if not self.ok:
            raise RestoreFailed(self)
