import requests

import rcbu.common.status as status


_predicates = {
    "backup_history": lambda j: j['Type'] == 'Backup' and not _is_running(j),
    "restore_history": lambda j: j['Type'] == 'Restore' and not _is_running(j),
    "active_backups": lambda j: j['Type'] == 'Backup' and _is_running(j),
    "active_restores": lambda j: j['Type'] == 'Restore' and _is_running(j),
    "active": lambda j: _is_running(j)
}


def _is_running(job):
    return status.busy(job['CurrentState'])


def _jobs(host, key, predicate, agent_id=None):
    url = ('{0}/{1}'.format(host, 'activity') if not agent_id else
           '{0}/{1}/{2}/{3}'.format(host, 'system', 'activity', agent_id))
    headers = {'x-auth-token': key}
    resp = requests.get(url, headers=headers, verify=False)
    resp.raise_for_status()
    return [b for b in resp.json() if predicate(b)]


def _any_running(host, key, agent_id=None):
    return len(_jobs(host, key, _predicates['active'], agent_id)) > 0


class ExposesActivities(object):
    def __init__(self, host, key, oid=None):
        self._host = host
        self._key = key
        self._id = oid

    @property
    def backup_history(self):
        return _jobs(self._host, self._key,
                     _predicates['backup_history'], self._id)

    @property
    def restore_history(self):
        return _jobs(self._host, self._key,
                     _predicates['restore_history'], self._id)

    @property
    def active_backups(self):
        return _jobs(self._host, self._key,
                     _predicates['active_backups'], self._id)

    @property
    def active_restores(self):
        return _jobs(self._host, self._key,
                     _predicates['active_restores'], self._id)

    @property
    def busy(self):
        return _any_running(self._host, self._key, self._id)
