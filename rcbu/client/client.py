import requests

import rcbu.common.factory as factory
from rcbu.common.auth import authenticate
from rcbu.common.show import Show


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
        return '{}:{}'.format('RCBU Connection', self.endpoint)

    @property
    def agents(self):
        url = self.endpoint + '/user/agents'
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        body = resp.json()
        return [factory.agent_from_response(agent, self) for agent in body]

    @property
    def backup_configurations(self):
        url = self.endpoint + '/backup-configuration'
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        body = resp.json()
        return [factory.backup_config_from_response(config, self)
                for config in body]

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
    def active_backups(self):
        url = self.endpoint + '/activity'
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return [backup for backup in resp.json()
                if backup['Type'] == 'Backup']

    @property
    def active_restores(self):
        url = self.endpoint + '/activity'
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return [backup for backup in resp.json()
                if backup['Type'] == 'Restore']

    def get_agent(self, agent_id):
        url = '{}/{}/{}'.format(self.endpoint, 'agent', agent_id)
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return resp.json()

    def get_backup_configuration(self, config_id):
        url = '{}/{}/{}'.format(self.endpoint, 'backup-configuration',
                                config_id)
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return factory.backup_config_from_response(resp.json(), self)

    def get_backup_report(self, backup_id):
        url = '{}/{}/{}/{}'.format(self.endpoint, 'backup', 'report',
                                   backup_id)
        headers = {'x-auth-token': self.token}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return resp.json()

    def create_backup(self, config_id):
        pass

    def create_restore(self, config_id):
        pass
