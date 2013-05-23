import requests

from rcbu.common.auth import authenticate
from rcbu.common.show import Show
from rcbu.common.jobs import is_running
import rcbu.client.backup_configuration as backup_config
import rcbu.client.agent as agent
import rcbu.client.backup as backup
import rcbu.client.restore as restore


def _normalize_endpoint(url):
    idx = url.rfind('/')
    return url[:idx]


def _find_backup_endpoint(endpoints):
    target = None
    for entry in endpoints:
        if entry['type'] == 'rax:backup':
            target = entry
            break
    return _normalize_endpoint(target['endpoints'][0]['publicURL'])


class Connection(Show):

    def __init__(self, username, apikey=None, password=None):
        resp = None
        assert apikey or password

        if apikey:
            resp = authenticate(username, apikey=apikey)
        else:
            resp = authenticate(username, password=password)

        self.token = resp['access']['token']['id']
        endpoints = resp['access']['serviceCatalog']
        self.endpoint = _find_backup_endpoint(endpoints)

    def __str__(self):
        return '{0}:{1}'.format('RCBU Connection', self.endpoint)

    @property
    def agents(self):
        url = self.endpoint + '/user/agents'
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        body = resp.json()
        return [agent.from_dict(a, connection=self) for a in body]

    @property
    def backup_configurations(self):
        url = self.endpoint + '/backup-configuration'
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        body = resp.json()
        return [backup_config.from_dict(config, self) for config in body]

    @property
    def host(self):
        return self.endpoint

    @property
    def api_version(self):
        return self.endpoint.split('/')[-1].lstrip('v')

    @property
    def api_version_tuple(self):
        return tuple(int(i) for i in self.api_version.split('.'))

    def _jobs(self, predicate):
        url = self.endpoint + '/activity'
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return [b for b in resp.json() if predicate(b)]

    @property
    def backup_history(self):
        return self._jobs(lambda job: job['Type'] == 'Backup' and
                          not is_running(job))

    @property
    def restore_history(self):
        return self._jobs(lambda job: job['Type'] == 'Restore' and
                          not is_running(job))

    @property
    def active_backups(self):
        return self._jobs(lambda job: job['Type'] == 'Backup' and
                          is_running(job))

    @property
    def active_restores(self):
        return self._jobs(lambda job: job['Type'] == 'Restore' and
                          is_running(job))

    def get_agent(self, agent_id):
        url = '{0}/{1}/{2}'.format(self.endpoint, 'agent', agent_id)
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return agent.from_dict(resp.json(), connection=self)

    def get_backup_configuration(self, config_id):
        url = '{0}/{1}/{2}'.format(self.endpoint, 'backup-configuration',
                                   config_id)
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return backup_config.from_dict(resp.json())

    def get_backup_report(self, backup_id):
        url = '{0}/{1}/{2}/{3}'.format(self.endpoint, 'backup', 'report',
                                       backup_id)
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return resp.json()

    def create_backup(self, config):
        backup_action = backup.Backup(config, connection=self)
        return backup_action

    def create_restore(self, backup, source_agent, destination_path,
                       destination_agent=None, overwrite=False):
        raise NotImplementedError()
        if not destination_agent:
            destination_agent = source_agent
        restore_action = restore.Restore(backup, source_agent,
                                         destination_path,
                                         destination_agent, overwrite)
        return restore_action
