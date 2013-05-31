from rcbu.client.report import Report
from rcbu.common.exceptions import BackupFailed


def _args_from_dict(body):
    args = {
        '_config_id': body['BackupConfigurationId'],
        '_config_name': body['BackupConfigurationName'],
        '_agent_id': body['MachineAgentId'],
        '_machine_name': body['ComputerName'],
        '_state': body['State'],
        '_restorable': body['CanRestore'],
        '_time': {
            'start': body['StartTime'],
            'end': body['CompletedTime'],
            'duration': body['Duration']
        },
        '_searched': {
            'files': body['FilesSearched'],
            'bytes': body['BytesSearched']
        },
        '_backup': {
            'files': body['FilesBackedUp'],
            'bytes': body['BytesBackedUp']
        },
        '_num_errors': body['NumErrors'],
        '_outcome': body['Reason'],
        '_diagnostics': body['Diagnostics'],
        '_errors': body['ErrorList']
    }
    return args


def from_dict(body, connection=None):
    args = _args_from_dict(body)
    return BackupReport(body['BackupId'], connection, **args)


class BackupReport(Report):
    def __init__(self, backup_id, connection=None, **kwargs):
        self.backup_id = backup_id
        self._connection = connection
        [setattr(self, k, v) for k, v in kwargs.items()]

    @property
    def id(self):
        return self.backup_id

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
            raise BackupFailed(self)
