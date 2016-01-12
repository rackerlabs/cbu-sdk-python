"""
Rackspace Cloud Backup RSE API
"""
import logging
import pprint
import requests
import time
import uuid

import cloudbackup.client.auth
import cloudbackup.client.agents
from cloudbackup.common.command import Command

requests.packages.urllib3.disable_warnings()


class RseData(object):
    """
    Class to manage the RSE specific data, namely the UUID and User Agent in an easy manner
    """

    def __init__(self, app, appVersion):
        """
        Initialize the RseData
          app - string with the name of the application, f.e 'myApp'
          appVersion - string with the version number of the application, f.e 'v1.2'
        """
        self.log = logging.getLogger(__name__)
        self.app = app
        self.appVersion = appVersion
        # UUID needs to change with every app version. uuid.uuid5 gives us an easy way to do that
        self.uuid = uuid.uuid5(uuid.NAMESPACE_URL, ('python.sdk.cloudbackup.rackspace.com/' + self.app + '/' + self.appVersion))
        # Build the User Agent expected by RSE
        # IT MUST HAVE 3 SECTIONS DELIMITED BY '/'
        # SECTION 1 MAY BE ANY NAME
        # SECTION 2 MUST HAVE A VERSION NUMBER AND END WITH uuid
        # SECTION 3 MUST BE A DASH-DELIMITED GUID
        self.userAgent = self.app + '/' + self.appVersion + ' uuid/' + str(self.uuid)
        self.log.debug('RSE User-Agent: ' + self.userAgent)

    @property
    def RseUserAgent(self):
        """
        return the User-Agent to be used with RSE
        """
        return self.userAgent

    @property
    def Uuid(self):
        """
        return the UUID to be used with RSE
        """
        return self.uuid

    @property
    def App(self):
        """
        return the application name that was specific during construction
        """
        return self.app

    @property
    def AppVersion(self):
        """
        return the application version that was specified during construction
        """
        return self.appVersion


class Rse(Command):
    """
    Object defining HTTP REST API calls for interacting with Rackspace RSE
    """

    def __init__(self, app, appversion, authenticator, agent, agentkey,
                 logfile=None, apihost=None, api_version=1, project_id=None):
        """
        Initialize the Rse access
          app - the application name to use with Rse
          appversion - the application version to use with Rse
          authenticator - instance of cloudbackup.client.auth.Authentication to use
          agent - instance of cloudbackup.client.agents.Agent to use - assumes the agent instance already queried for the RSE data
          agentkey - agent's RSE Channel
          logfile - (optional) filename to log the RSE transactions to
          apihost - (optional) URI of the Rackspace Cloud Backup API Host; if specified then RSE messaging will go through the API
          api_version - required if apihost is specified
          project_id - required if Rackspace Cloud Backup API is newer than Version 1.x

        Note: If apihost is specified then the cloudbackup.client.rse.Rse instance will mimick the Cloud Backup Control Panel and
            use the Cloud Backup API as a means to get the RSE messages. If it is not specified, then it will talk to the RSE
            service for the agent directly.
        """
        # do not pass the info here as it will change based on the agent information when a call is actually made
        # RSE data is always over HTTPS
        super(self.__class__, self).__init__(True, 'localhost', '/')
        self.log = logging.getLogger(__name__)
        self.rsedata = cloudbackup.client.rse.RseData(app, appversion)
        self.sslenabled = True
        self.authenticator = authenticator
        self.agent = agent
        self.agentkey = agentkey
        self.rselogfile = logfile
        self.apihost = apihost
        self.api_version = api_version
        self.project_id = project_id

    def RseInitDirect(self, machine_agent_id):
        """
        Reinitialize the command data and add the appropriate RSE data
          ** Internal Use Only **

        Note: Directly interacts with RSE
        """
        self.apihost = self.agent.GetRseHost(machine_agent_id)
        self.ReInit(self.sslenabled, self.agent.GetRseChannel(machine_agent_id))
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['X-Agent-Key'] = self.agentkey
        # RSE version is hard coded and must be changed when a newer version of RSE is to be used
        self.headers['X-RSE-Version'] = '2011-05-01'
        # This really matters when we are talkingw ith RSE
        self.headers['User-Agent'] = self.rsedata.RseUserAgent

    def RseInitIndirect(self, machine_agent_id):
        """
        Reinitialize the command data and add the appropriate RSE data

        Note: Indirectly interacts with RSE via the API
        """
        if self.api_version == 1:
            self.ReInit(self.sslenabled,
                        '/v1.0/agent/events/{0}'.format(machine_agent_id))
        else:
            self.ReInit(self.sslenabled,
                        '/v{0}/{1}/agents/{2}/events/'.format(
                            self.api_version, self.project_id,
                            machine_agent_id))
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken

    def RseInit(self, machine_agent_id):
        """
        Reinitialize for the machine agent.
        If apihost is set, then indirectly access RSE - all events are received on the channel for all systems talking on the channel
        If apihost is not set, then directly access RSE - only events to the desired agent are received on the channel
        """
        if self.apihost is None:
            self.RseInitDirect(machine_agent_id)
        else:
            self.RseInitIndirect(machine_agent_id)

    def Query(self):
        """
        Retrieves one record set from the RSE Channel
        """
        res = requests.get(self.Uri, headers=self.Headers)
        self.log.debug('RSE Query: Code (%s)', res.status_code)
        if not self.rselogfile is None:
            with open(self.rselogfile, 'a') as out:
                out.write('=======================================================================\n')
                out.write('Time: ' + time.strftime('%Y-%m-%d %H:%M:%S %Z') + '\n')
                out.write('Status Code: ' + str(res.status_code) + '\n')
                out.write('Result Text:\n')
                out.write('-----------------------------------------------------------------------\n')
                pprint.pprint(res.text, stream=out)
                out.write('\n-----------------------------------------------------------------------\n')
                out.write('Result JSON:\n')
                out.write('-----------------------------------------------------------------------\n')
                if (res.status_code == 200):
                    pprint.pprint(res.json(), stream=out)
                else:
                    out.write('--- invalid json returned ---')
                out.write('\n-----------------------------------------------------------------------\n')

        if (res.status_code == 200):
            return res.json()
        else:
            return {}

    def MonitorForHeartBeat(self, machine_agent_id):
        """
        Check the RSE Channel Data for the Heart Beat message from a given agent
        """
        try:
            # Build the URI for the given agent we are looking for
            self.RseInit(machine_agent_id)
            # Poll RSE
            rsemsg = self.Query()
            if 'events' in rsemsg:
                # Find the heart beat messages and determine if there is one
                # for the specified agent
                for event in rsemsg['events']:
                    if not self.rselogfile is None:
                        with open(self.rselogfile, 'a') as out:
                            out.write('(RSE) Message: ')
                            out.write(str(event))
                            out.write('\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n')
                    if self.api_version == 1:
                        if event['data']['Event'] == 'Heartbeat':
                            if (event['data']['MachineAgentId'] == 
                                    machine_agent_id and event['age'] < 26):
                                return True
                    else:
                        if event['event'] in ('heartbeat', 'agent_heartbeat'):
                            return True
                return False
            else:
                for event in rsemsg:
                    if not self.rselogfile is None:
                        with open(self.rselogfile, 'a') as out:
                            out.write('(API) Message: ')
                            out.write(str(event))
                            out.write('\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n')
                    if event['data']['Event'] == 'Heartbeat':
                        if event['data']['MachineAgentId'] == machine_agent_id and event['age'] < 26:
                            return True
                self.log.error('invalid RSE message received')
                return False
        except LookupError:
            self.log.error('error while parsing RSE data')
            return False
