#!/usr/bin/python
from __future__ import print_function

import argparse
import json
import logging
import sys

import six

import cloudbackup.client.agents
import cloudbackup.client.auth
import cloudbackup.utils.menus

class CloudBackupApiShellException(Exception):
    pass

class CloudBackupApiBadParameters(CloudBackupApiShellException):
    pass


class CloudBackupApiBadAuthData(CloudBackupApiShellException):
    pass


class CloudBackupApiShell(object):

    def __init__(self, logger, auth_data_file, datacenter, use_servicenet=False):
        if datacenter not in ('ord', 'syd', 'hkg', 'iad', 'dfw', 'lon'):
            raise CloudBackupApiBadParameters(
                'Invalid Datacenter - {0}'.format(datacenter))

        self.api = {}
        self.auth_data = {}
        self.log = logger
        self.datacenter = datacenter
        self.use_servicenet = use_servicenet

        self.auth_data['file'] = auth_data_file
        self.auth_data['json'] = json.load(self.auth_data['file'])

        self.auth_data['user_type'] = 'user'
        self.auth_data['user'] = self.auth_data['json']['user']

        self.auth_data['user_type'] = 'user'
        if 'user_type' in self.auth_data['json']:
            self.auth_data['user_type'] = self.auth_data['json']['user_type']

        if self.auth_data['user_type'] not in (
                'user', 'tenantid', 'tenantname'):
            raise CloudBackupApiBadAuthData(
                'invalid user type {0}'.format(
                    self.auth_data['user_type']))

        if 'token' in self.auth_data['json']:
            self.auth_data['method'] = 'token' 
            self.auth_data['credentials'] = self.auth_data['json']['token']

        elif 'apikey' in self.auth_data['json']:
            self.auth_data['method'] = 'apikey' 
            self.auth_data['credentials'] = self.auth_data['json']['apikey']

        elif 'password' in self.auth_data['json']:
            self.auth_data['method'] = 'password'
            self.auth_data['credentials'] = self.auth_data['json']['password']

        else:
            raise CloudBackupApiBadAuthData('invalid json file')

        # Build the Auth Engine
        self.auth_engine = cloudbackup.client.auth.Authentication(
            self.auth_data['user'],
            self.auth_data['credentials'],
            usertype=self.auth_data['user_type'],
            method=self.auth_data['method'],
            datacenter=self.datacenter
        )

        # Get the URI for Cloud Backup API
        self.api['uri'] = self.auth_engine.GetCloudBackupApiUri(
            self.datacenter,
            self.use_servicenet
        )
        # TODO: Add support for Test/Pre-Prod API

        self.agents = cloudbackup.client.agents.Agents(
            True,  # use HTTPS
            self.auth_engine,
            self.api['uri'],
            self.auth_engine.GetCloudBackupApiVersion(
                self.datacenter,
                self.use_servicenet),
            self.auth_engine.AuthTenantId
        )

    def GetAgentIds(self):
        self.api['available-agents'] = self.agents.GetAgentsFromApi()
        return self.api['available-agents']

    def GetAgentIdFromUser(self):
        agent_menu = []
        for agent_id in self.GetAgentIds():
            agent_id_entry = {
                'index': len(agent_menu),
                'text': '{0}'.format(agent_id),
                'type': 'agent-id'
            }
            agent_menu.append(agent_id_entry)
        agent_menu.append({
            'index': len(agent_menu),
            'text': 'Exit',
            'type': 'EXIT'
        })
        selection = cloudbackup.utils.menus.promptSelection(
            agent_menu,
            'Select Agent ID'
        )
        return selection

    def WorkOnAgent(self, active_agent_id):
        # do the negative test so that we can dedicate more space to the 
        # positive result and make readability nicer
        if not self.agents.GetAgentDetails(active_agent_id):
            msg = 'Failed to retrieve agent details for agent id {0}'.format(
                active_agent_id
            )
            self.log.error(msg)
            print(msg)

        else:
            agent_details = self.agents.AgentDetails(active_agent_id)
            while True:
                print('Agent Details:')
                print('\tAgent ID: {0}'.format(agent_details.agent_id))
                print('\tAgent Version: {0}'.format(agent_details.AgentVersion))

                # menu
                agent_detail_menu = [
                    { 'index': 1, 'text': 'Show Details', 'type': 'details' },
                    { 'index': 2, 'text': 'Access Configuration', 'type': 'configuration' },
                    { 'index': 3, 'text': 'Return to previous menu', 'type': 'returnToPrevious' }
                ]

                selection = cloudbackup.utils.menus.promptSelection(
                    agent_detail_menu,
                    'Selection Action'
                )
                if selection['type'] == 'returnToPrevious':
                    return

                elif selection['type'] == 'details':
                    print('Agent Details:')
                    print('\tAgent ID: {0}'.format(agent_details.agent_id))
                    print('\tAgent Version: {0}'.format(agent_details.AgentVersion))
                    print('\tVault Encrypted: {0}'.format( 'YES' if agent_details.IsEncrypted else 'NO'))
                    print('\tAgent Status: {0}'.format('ENABLED' if agent_details.IsEnabled else 'DISABLED'))
                    print()
                    print('\tDatacenter: {0}'.format(agent_details.Datacenter))
                    print('\tFlavor: {0}'.format(agent_details.Flavor))
                    print('\tSystem Name: {0}'.format(agent_details.MachineName))
                    print('\tServer Identifier: {0}'.format(agent_details.HostServerId))
                    print('\tArchitecture: {0}'.format(agent_details.Architecture))
                    print('\tOperating System: {0}'.format(agent_details.OperatingSystem))
                    print('\tSystem IP Addresses (IPv4):')
                    for ipv4_address in [agent_details.IPAddress]:
                        print('\t\t{0}'.format(ipv4_address))
                    print('\n')

                elif selection['type'] == 'configuration':
                    pass

    def doShell(self):
        while True:
            # Note: there is presently no paging in this menu selection
            agent_selection = self.GetAgentIdFromUser()
            if agent_selection['type'] == 'EXIT':
                return 0

            else:
                self.WorkOnAgent(agent_selection['text'])


def main():
    return_value = 0

    argument_parser = argparse.ArgumentParser(description='Cloud Backup Api Shell')
    argument_parser.add_argument('--user-config', default=None, type=argparse.FileType('r'), required=True, help='JSON file containing username and API Key')
    argument_parser.add_argument('-dc', '--datacenter', default='ord', type=str, required=True, help='Datacenter the system is in', choices=['lon', 'syd', 'hkg', 'ord', 'iad', 'dfw'])
    argument_parser.add_argument('-lg', '--log-config', default=None, type=str, dest='logconfig', help='log configuration file')
    argument_parser.add_argument('--use-snet', default=False, action='store_true', help='Use Service Net instead of Public Net')

    arguments = argument_parser.parse_args()

    # If the caller provides a log configuration then use it
    # Otherwise we'll add our own little configuration as a default
    # That captures stdout and outputs to .agent_unique_constraint_fix-py.log
    if arguments.logconfig is not None:
        logging.config.fileConfig(arguments.logconfig)
    else:
        lf = logging.FileHandler('.rackspace-cloud-backup-api-shell.log')
        lf.setLevel(logging.DEBUG)

        log = logging.getLogger()
        log.addHandler(lf)
        log.setLevel(logging.DEBUG)

    log = logging.getLogger()

    shell = CloudBackupApiShell(
        log,
        arguments.user_config,
        arguments.datacenter,
        use_servicenet=arguments.use_snet
    )

    return_value = shell.doShell()

    return return_value


if __name__ == "__main__":
    sys.exit(main())
