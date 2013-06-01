import rcbu.client.report as report
from rcbu.common.exceptions import RestoreFailed


def _args_from_dict(body):
    args = {
        '_backup_id': body['BackupConfigurationId'],
        '_restored': {
            'files': body['NumFilesRestored'],
            'bytes': body['NumBytesRestored']
        },
        '_destination': {
            'id': body['RestoreDestinationMachineId'],
            'name': body['RestoreDestination']
        }
    }
    args.update(report._args_from_dict(body))
    return args


def from_dict(restore_id, body):
    args = _args_from_dict(body)
    return RestoreReport(restore_id, **args)


class RestoreReport(Report):
    def __init__(self, report_id, **kwargs):
        Report.__init__(self, report_id, kwargs)

    @property
    def files_restored(self):
        return self._restored['files']

    @property
    def bytes_restored(self):
        return self._restored['bytes']
