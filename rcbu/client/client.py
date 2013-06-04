import json

import requests

from rcbu.common.show import Show
from rcbu.common.activity_mixin import ExposesActivities
import rcbu.client.backup_configuration as backup_config
import rcbu.client.agent as agent
import rcbu.client.backup as backup
import rcbu.client.restore as restore


class Client(Show, ExposesActivities):
    def __init__(self, connection):
        self._connection = connection
        ExposesActivities.__init__(self, self._connection.endpoint,
                                   self._connection.token)

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
        headers = {'x-auth-token': self.token,
                   'content-type': 'application/json'}
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
