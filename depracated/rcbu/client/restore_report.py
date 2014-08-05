import rcbu.client.report as report
from rcbu.utils.bytes import dehumanize_bytes
import rcbu.common.duration as duration


def _args_from_dict(body):
    args = {
        '_backup_id': body['BackupConfigurationId'],
        '_restored': {
            'files': int(body['NumFilesRestored']),
            'bytes': body['NumBytesRestored']
        },
        '_destination': {
            'id': body['RestoreDestinationMachineId'],
            'path': body['RestoreDestination']
        }
    }
    args.update(report._args_from_dict(body))
    return args


def from_dict(restore_id, body):
    args = _args_from_dict(body)
    return RestoreReport(restore_id, **args)


class RestoreReport(report.Report):
    def __init__(self, report_id, **kwargs):
        report.Report.__init__(self, report_id, 'restore', **kwargs)

    def __repr__(self):
        form = ('<RestoreReport id:{0} state:{1} ok:{2} started:{3} '
                'duration:{4} #errors:{5} bytes:{6}>')
        hours, minutes, seconds = duration.tuple(self.duration)
        return form.format(self.id, self.state, self.ok,
                           self.started.isoformat(),
                           '{0}:{1:02}:{2:02}'.format(hours, minutes, seconds),
                           len(self.errors), self.bytes_restored)

    @property
    def files_restored(self):
        return self._restored['files']

    @property
    def bytes_restored(self):
        return dehumanize_bytes(self._restored['bytes'])

    @property
    def destination(self):
        """Returns a string in the form: 'path id'"""
        return '{0} {1}'.format(self._destination['path'],
                                self._destination['id'])
