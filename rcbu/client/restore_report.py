from rcbu.client.report import Report


def _args_from_dict(body):
    return {
        '_config_id': body['BackupConfigurationId'],
        '_config_name': body['BackupConfigurationName'],
        '_backup_id': body['BackupConfigurationId'],
        '_state': body['State'],
        '_time': {
            'start': body['StartTime'],
            'end': body['CompletedTime'],
            'duration': body['Duration']
        },
        '_restored': {
            'files': body['NumFilesRestored'],
            'bytes': body['NumBytesRestored']
        },
        '_destination': {
            'id': body['RestoreDestinationMachineId'],
            'name': body['RestoreDestination']
        },
        '_num_errors': body['NumErrors'],
        '_outcome': body['Reason'],
        '_diagnostics': body['Diagnostics'],
        '_errors': body['ErrorList']
    }


def from_dict(restore_id, body):
    args = _args_from_dict(body)
    return RestoreReport(restore_id, **args)


class RestoreFailed(Exception):
    def __init__(self, report):
        self.message = '{0}:{1}'.format(report._diagnostics, report.errors)


class RestoreReport(Report):
    def __init__(self, restore_id, **kwargs):
        self._id = restore_id
        [setattr(self, k, v) for k, v in kwargs.items()]

    @property
    def id(self):
        return self._id

    @property
    def errors(self):
        return self._errors

    @property
    def outcome(self):
        return self._outcome

    @property
    def ok(self):
        return len(self.errors) == 0

    def raise_if_not_ok(self):
        if not self.ok:
            raise RestoreFailed(self)
