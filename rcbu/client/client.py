import requests

from rcbu.common.auth import authenticate
from rcbu.common.show import Show
import rcbu.client.backup_configuration as backup_config
import rcbu.client.agent as agent
import rcbu.client.backup as backup
import rcbu.client.restore as restore
import rcbu.common.jobs as jobs


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

    @property
    def backup_history(self):
        return jobs.backup_history(self.endpoint, self.token)

    @property
    def restore_history(self):
        return jobs.restore_history(self.endpoint, self.token)

    @property
    def active_backups(self):
        return jobs.active_backups(self.endpoint, self.token)

    @property
    def active_restores(self):
        return jobs.active_restores(self.endpoint, self.token)

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

    def create_restore(self, backup_id, source_agent, destination_path,
                       destination_agent=None, overwrite=False):
        url = '{0}/{1}'.format(self.endpoint, 'restore')
        headers = {'x-auth-token': self.token}
        data = json.dumps({
            'BackupId': backup_id,
            'BackupMachineId': source_agent.id,
            'DestinationMachineId': (source_agent.id if not destination_agent
                                     else destination_agent.id),
            'DestinationPath': destination_path,
            'OverwriteFiles': overwrite
        })
        resp = requests.put(url, headers=headers, data=data, verify=False)
        resp.raise_for_status()
        restore_action = restore.from_dict(resp.json(), connection=self)
        return restore_action
