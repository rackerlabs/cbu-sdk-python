import rcbu.common.status as status
import rcbu.common.activity as activity
from rcbu.common.http import Http


_predicates = {
    "backup_history": lambda j: j['Type'] == 'Backup' and not _is_running(j),
    "restore_history": lambda j: j['Type'] == 'Restore' and not _is_running(j),
    "cleanup_history": lambda j: j['Type'] == 'Cleanup' and not _is_running(j),
    "active_backups": lambda j: j['Type'] == 'Backup' and _is_running(j),
    "active_restores": lambda j: j['Type'] == 'Restore' and _is_running(j),
    "active_cleanups": lambda j: j['Type'] == 'Cleanup' and _is_running(j),
    "active": lambda j: _is_running(j),
    "not_active": lambda j: not _is_running(j)
}


def _is_running(job):
    return status.busy(job['CurrentState'])


def _jobs(connection, predicate, agent_id=None):
    url = ('{0}/activity'.format(connection.host) if agent_id is None else
           '{0}/system/activity/{1}'.format(connection.host, agent_id))
    resp = connection.request(Http.get, url, verify=False)
    resp.raise_for_status()
    return (activity.from_dict(b) for b in resp.json() if predicate(b))


def _any_running(connection, agent_id=None):
    try:
        next(_jobs(connection, _predicates['active'], agent_id))
    except StopIteration:
        return False
    return True


class ExposesActivities(object):
    def __init__(self, connection, oid=None):
        self._connection = connection
        self._id = oid

    def _listing(self, predicate):
        return _jobs(self._connection, predicate, self._id)

    @property
    def backup_history(self):
        return self._listing(_predicates['backup_history'])

    @property
    def restore_history(self):
        return self._listing(_predicates['restore_history'])

    @property
    def cleanup_history(self):
        return self._listing(_predicates['cleanup_history'])

    @property
    def active_backups(self):
        return self._listing(_predicates['active_backups'])

    @property
    def active_restores(self):
        return self._listing(_predicates['active_restores'])

    @property
    def active_cleanups(self):
        return self._listing(_predicates['active_cleanups'])

    @property
    def active(self):
        return self._listing(_predicates['active'])

    @property
    def history(self):
        return self._listing(_predicates['not_active'])

    @property
    def busy(self):
        return _any_running(self._connection, self._id)
