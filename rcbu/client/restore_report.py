from rcbu.client.report import Report


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


class RestoreFailed(Exception):
    def __init__(self, report):
        self.message = '{0}:{1}'.format(report._diagnostics, report.errors)


class RestoreReport(Report):
    def __init__(self, restore_id):
        self._id = restore_id

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
        return self._restorable

    def raise_if_not_ok(self):
        if not self.ok:
            raise RestoreFailed(self)
