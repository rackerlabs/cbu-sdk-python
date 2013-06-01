import rcbu.client.report as report


def _args_from_dict(body):
    args = {
        '_agent_id': body['MachineAgentId'],
        '_machine_name': body['ComputerName'],
        '_restorable': body['CanRestore'],
        '_searched': {
            'files': body['FilesSearched'],
            'bytes': body['BytesSearched']
        },
        '_backup': {
            'files': body['FilesBackedUp'],
            'bytes': body['BytesBackedUp']
        }
    }
    args.update(report._args_from_dict(body))
    return args


def from_dict(backup_id, body):
    args = _args_from_dict(body)
    return BackupReport(backup_id, **args)


class BackupReport(report.Report):
    def __init__(self, report_id, **kwargs):
        report.Report.__init__(self, report_id, 'backup', **kwargs)

    @property
    def ok(self):
        return self._restorable

    @property
    def files_searched(self):
        return self._searched['files']

    @property
    def bytes_searched(self):
        return self._searched['bytes']

    @property
    def files_stored(self):
        return self._backup['files']

    @property
    def bytes_stored(self):
        return self._backup['bytes']
