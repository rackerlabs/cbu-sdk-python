from __future__ import print_function

import argparse
import json
import logging
import logging.config
import random
import sys
import time

import six

import cloudbackup.client.agents
import cloudbackup.client.auth
import cloudbackup.client.backup
import cloudbackup.client.rse
import cloudbackup.cmd.shell.exceptions
import cloudbackup.cmd.shell.prompter as prompt_user
import cloudbackup.utils.menus
from cloudbackup.utils import tz

class CloudBackupApiShell(object):

    def __init__(self, logger, auth_data_file, datacenter, use_servicenet=False):
        if datacenter not in ('ord', 'syd', 'hkg', 'iad', 'dfw', 'lon'):
            raise cloudbackup.cmd.shell.exceptions.CloudBackupApiBadParameters(
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
            raise cloudbackup.cmd.shell.exceptions.CloudBackupApiBadAuthData(
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
            raise cloudbackup.cmd.shell.exceptions.CloudBackupApiBadAuthData('invalid json file')

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
        self.log.debug('Cloud Backup API URI: {0}'.format(self.api['uri']))
        self.api['version'] = self.auth_engine.GetCloudBackupApiVersion(
            self.datacenter,
            self.use_servicenet
        )
        self.log.debug('Cloud Backup API Version: {0}'.format(self.api['version']))
        # TODO: Add support for Test/Pre-Prod API

        self.agents = cloudbackup.client.agents.Agents(
            True,  # use HTTPS
            self.auth_engine,
            self.api['uri'],
            self.api['version'],
            self.auth_engine.AuthTenantId
        )

        self.backup_engine = cloudbackup.client.backup.Backups(
            True,  # use HTTPS
            self.auth_engine,
            self.api['uri'],
            self.api['version'],
            self.auth_engine.AuthTenantId
        )

        self.rse = None
        self.snapshot_ids = {}

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

    def doCreateV1BackupConfiguration(self, active_agent_id, config_data):
        DayOfWeekMapping = {
            'Sunday': 0,
            'Monday': 1,
            'Tuesday': 2,
            'Wednesday': 3,
            'Thursday': 4,
            'Friday': 5,
            'Saturday': 6
        }

        backup_config = cloudbackup.client.backup.BackupConfiguration()

        # Convert from 24-hour Format to 12-hour AM/PM Format
        if config_data['schedule']['start-time']['hour'] == 0:
            config_data['schedule']['start-time']['hour'] = 12
            config_data['schedule']['start-time']['am-pm'] = 'AM'

        elif config_data['schedule']['start-time']['hour'] == 12:
            config_data['schedule']['start-time']['am-pm'] = 'PM'

        elif config_data['schedule']['start-time']['hour'] in range(13, 24):
            config_data['schedule']['start-time']['hour'] = config_data['schedule']['start-time']['hour'] - 12
            config_data['schedule']['start-time']['am-pm'] = 'PM'

        elif config_data['schedule']['start-time']['hour'] in range(1,12):
            config_data['schedule']['start-time']['am-pm'] = 'AM'

        backup_config.ConfigurationName = config_data['name']
        backup_config.MachineAgentId = int(active_agent_id)
        backup_config.Active = True
        backup_config.VersionRetention = config_data['retention']
        backup_config.Frequency = config_data['schedule']['frequency']
        backup_config.StartTimeHour = config_data['schedule']['start-time']['hour']
        backup_config.StartTimeMinute = config_data['schedule']['start-time']['minute']
        backup_config.StartTimeAmPm = config_data['schedule']['start-time']['am-pm']
        if not config_data['schedule']['day-of-week'] is None:
            backup_config.DayOfWeekId = DayOfWeekMapping[
                config_data['schedule']['day-of-week']
            ]
        else:
            backup_config.DayOfWeekId = None
        if config_data['schedule']['frequency'] == 'HOURLY':
            backup_config.HourInterval = config_data['schedule']['hourly-interval']
        if config_data['schedule']['start-time']['timezone'] is not None:
            backup_config.TimeZoneId = config_data['schedule']['start-time']['timezone']
        else:
            backup_config.TimeZoneId = tz.get_timezone(
                self.api['version'] == 1
            )
        backup_config.NotifyRecipients = config_data['notifications']['e-mail-addresses'][0]
        backup_config.NotifySuccess = config_data['notifications']['success']
        backup_config.NotifyFailure = config_data['notifications']['failure']
        for item_name, item_type in config_data['paths']['inclusions']:
            if item_type == 'file':
                backup_config.AddFile(item_name, excluded=False)
            else:
                backup_config.AddFolder(item_name, excluded=False)
        for item_name, item_type in config_data['paths']['exclusions']:
            if item_type == 'file':
                backup_config.AddFile(item_name, excluded=True)
            else:
                backup_config.AddFolder(item_name, excluded=True)
        if not self.backup_engine.CreateBackupConfiguration(
                backup_config):
            print('Failed to create backup configuration. See logs for details')

    def doCreateV2BackupConfiguration(self, active_agent_id, config_data):
        DayOfWeekMapping = {
            'Sunday': 'SU',
            'Monday': 'MO',
            'Tuesday': 'TU',
            'Wednesday': 'WE',
            'Thursday': 'TH',
            'Friday': 'FR',
            'Saturday': 'SA'
        }

        backup_config = cloudbackup.client.backup.BackupConfigurationV2()

        #random.seed()
        #backup_config.ConfigurationId = random.randint(100, 10000)
        backup_config.ConfigurationId = None
        backup_config.ConfigurationName = config_data['name']
        backup_config.MachineAgentId = active_agent_id
        backup_config.Active = True
        backup_config.VersionRetention = config_data['retention']
        backup_config.Frequency = config_data['schedule']['frequency']

        backup_config.StartTimeHour = config_data['schedule']['start-time']['hour']
        backup_config.StartTimeMinute = config_data['schedule']['start-time']['minute']
        if not config_data['schedule']['day-of-week'] is None:
            backup_config.DayOfWeekId = DayOfWeekMapping[
                config_data['schedule']['day-of-week']
            ]
        else:
            backup_config.DayOfWeekId = None

        # Note: This will either be 1 or the hourly frequency
        backup_config.Interval = config_data['schedule']['hourly-interval']

        backup_config.TimeZoneId = config_data['schedule']['start-time']['timezone']
        backup_config.NotifyRecipients = config_data['notifications']['e-mail-addresses'][0]
        backup_config.NotifySuccess = config_data['notifications']['success']
        backup_config.NotifyFailure = config_data['notifications']['failure']
        for item_name, item_type in config_data['paths']['inclusions']:
            if item_type == 'file':
                backup_config.AddFile(item_name, excluded=False)
            else:
                backup_config.AddFolder(item_name, excluded=False)
        for item_name, item_type in config_data['paths']['exclusions']:
            if item_type == 'file':
                backup_config.AddFile(item_name, excluded=True)
            else:
                backup_config.AddFolder(item_name, excluded=True)
        if not self.backup_engine.CreateBackupConfiguration(
                backup_config):
            print('Failed to create backup configuration. See logs for details')

    def doCreateBackupConfiguration(self, active_agent_id):
        def check_user_aborted(value):
            return value is None

        prompted_config_data = {
            'name': None,
            'schedule': {
                'frequency': None,
                'day-of-week': None,
                'start-time': {
                    'hour': None,
                    'minute': None,
                    'am-pm': None,
                    'timezone': tz.get_timezone(
                        self.api['version'] == 1
                    )
                },
                'hourly-interval': None
            },
            'retention': None,
            'notifications': {
                'e-mail-addresses': [],
                'success': False,
                'failure': True
            },
            'paths': {
                'inclusions': [],
                'exclusions': []
            }
        }
        user_aborted = False

        prompted_config_data['name'] = prompt_user.doPromptBackupConfigurationName(
            user_aborted
        )
        user_aborted = check_user_aborted(prompted_config_data['name'])

        frequency_data = prompt_user.doPromptFrequency(
            self.api['version'],
            user_aborted
        )
        user_aborted = check_user_aborted(frequency_data)
        if not user_aborted:
            prompted_config_data['schedule']['frequency'] = frequency_data['frequency']
            prompted_config_data['schedule']['day-of-week'] = frequency_data['dayOfWeek']
            prompted_config_data['schedule']['start-time']['hour'] = frequency_data['StartTime']['hour']
            prompted_config_data['schedule']['start-time']['minute'] = frequency_data['StartTime']['minute']
            prompted_config_data['schedule']['start-time']['am-pm'] = frequency_data['StartTime']['amOrPm']
            prompted_config_data['schedule']['start-time']['timezone'] = frequency_data['StartTime']['timeZone']
            prompted_config_data['schedule']['hourly-interval'] = frequency_data['interval']

        prompted_config_data['retention'] = prompt_user.doPromptRetention(
            user_aborted
        )

        notification_data = prompt_user.doPromptNotifications(
            user_aborted
        )
        user_aborted = check_user_aborted(notification_data)
        if not user_aborted:
            prompted_config_data['notifications']['e-mail-addresses'] = notification_data['addresses']
            prompted_config_data['notifications']['success'] = notification_data['onSuccess']
            prompted_config_data['notifications']['failure'] = notification_data['onFailure']

        inclusion_data = prompt_user.doPromptFilesAndFolders(
            user_aborted,
            inclusion=True
        )
        user_aborted = check_user_aborted(inclusion_data)
        if not user_aborted:
            prompted_config_data['paths']['inclusions'] = inclusion_data

        exclusion_data = prompt_user.doPromptFilesAndFolders(
            user_aborted,
            inclusion=False
        )
        user_aborted = check_user_aborted(exclusion_data)
        if not user_aborted:
            prompted_config_data['paths']['exclusions'] = exclusion_data

        if not user_aborted:
            if self.api['version'] == 1:
                self.doCreateV1BackupConfiguration(
                    active_agent_id,
                    prompted_config_data
                )

            elif self.api['version'] == 2:
                self.doCreateV2BackupConfiguration(
                    active_agent_id,
                    prompted_config_data
                )

            else:
                print('Unknown Cloud Backup API Version')
        else:
            print('User Aborted')

    def doPrintBackupConfigurationV1Details(self, active_agent_id, backup_config):
        print('Agent Configuration:')
        print('\tAgent ID: {0}'.format(active_agent_id))
        print('\t\t ID: {0}'.format(backup_config['Id']))
        print('\t\t Name: {0}'.format(backup_config['Name']))
        print('\t\t Enabled: {0}'.format(backup_config['IsEnabled']))
        print('\t\t Volume URI:')
        print('\t\t\tPrimary: {0}'.format(backup_config['VolumeUri']))
        print('\t\t\tSecondary: {0}'.format(backup_config['VolumeFailoverUri']))
        print('\t\t Scripts:')
        print('\t\t\tPre Script: {0}'.format(backup_config['BackupPrescript']))
        print('\t\t\tPost Script: {0}'.format(backup_config['BackupPostscript']))
        print('\t\t Data Retention:')
        print('\t\t\tPeriod: {0}'.format(backup_config['DaysToKeepOldFileVersions']))
        print('\t\t\tIndefinite: {0}'.format(backup_config['KeepOldFileVersionsIndefinitely']))
        print('\t\t Schedules: ')
        for schedule in backup_config['Schedules']:
            print('\t\t\tFrequency: {0}'.format(schedule['Frequency']))
            print('\t\t\tFirst Run: {0}'.format(schedule['InitialScheduledTime']))
            print('\t\t\tStart Time: {0}'.format(schedule['Start']))
            print('\t\t\tEnd Time: {0}'.format(schedule['End']))
            print('\t\t\tTime Zone Offset: {0}'.format(schedule['Offset']))
            print('\t\t\tObserve DST: {0}'.format(schedule['IsDST']))
            print('\t\t\tDay Of Week: {0}'.format(schedule['DayOfWeek']))
            print('\t\t\tHourly Interval: {0}'.format(schedule['HourlyInterval']))
            print('\t\t\tTime of Day: {0}'.format(schedule['TimeOfDay']))
        print('\t\t Included Files and Folders:')
        for inclusion in backup_config['Inclusions']:
            print('\t\t\tType: {0}'.format(inclusion['Type']))
            print('\t\t\tPattern: {0}'.format(inclusion['Pattern']))
            print('\t\t\tModule: {0}'.format(inclusion['Module']))
            print('\t\t\tArgs: {0}'.format(inclusion['Args']))
        print('\t\t Excluded Files and Folders:')
        for exclusion in backup_config['Exclusions']:
            print('\t\t\tType: {0}'.format(exclusion['Type']))
            print('\t\t\tPattern: {0}'.format(exclusion['Pattern']))
            print('\t\t\tModule: {0}'.format(exclusion['Module']))
            print('\t\t\tArgs: {0}'.format(exclusion['Args']))
        print('\n')

    def doPrintBackupConfigurationV2Details(self, active_agent_id, backup_config):
        print('Agent Configuration:')
        try:
            print('\tAgent ID: {0}'.format(active_agent_id))
            print('\t\t ID: {0}'.format(backup_config['id']))
            print('\t\t Name: {0}'.format(backup_config['name']))
            print('\t\t Enabled: {0}'.format(backup_config['enabled']))
            print('\t\t Vault ID: {0}'.format(backup_config['vault_id']))
            print('\t\t Data Retention:')
            print('\t\t\tPeriod: {0}'.format(backup_config['retention']['days']))
            print('\t\t Schedule: ')
            if backup_config['schedule'] is not None:
                print('\t\t\t Start: {0}'.format(backup_config['schedule']['start']))
                print('\t\t\t Time Zone: {0}'.format(backup_config['schedule']['time_zone']))
                print('\t\t\t Recurrence Rule(s):')
                for recurrence_rule in backup_config['schedule']['recurrence']:
                    print('\t\t\t\t{0}'.format(recurrence_rule))
                print('\t\t\t Next Backup Time: {0}'.format(backup_config['backups']['next']['scheduled_time']))
            else:
                print('\t\t\t Manual Backup')
            print('\t\t Included Files and Folders:')
            for inclusion in backup_config['inclusions']:
                print('\t\t\tType: {0}'.format(inclusion['type']))
                print('\t\t\tPath: {0}'.format(inclusion['path']))
            print('\t\t Excluded Files and Folders:')
            for exclusion in backup_config['exclusions']:
                print('\t\t\tType: {0}'.format(exclusion['type']))
                print('\t\t\tPath: {0}'.format(exclusion['path']))
        except:
            print('Error while decoding data.')
            print('RAW Backup Config: {0}'.format(backup_config))
            raise
        print('\n')

    def doPrintBackupConfigurationDetails(self, active_agent_id, backup_id, backup_name):
        backup_config = self.agents.AgentConfiguration(
            active_agent_id
        ).GetBackupConfigurationById(
            backup_id
        )

        if self.api['version'] == 1:
            self.doPrintBackupConfigurationV1Details(
                active_agent_id,
                backup_config
            )

        elif self.api['version'] == 2:
            self.doPrintBackupConfigurationV2Details(
                active_agent_id,
                backup_config
            )

        else:
            print('Unknown Cloud Backup API Version')

    def doPrintAgentGlobalConfiguration(self, active_agent_id, show_password=False):
        self.agents.GetAgentConfiguration(
            active_agent_id
        )

        agent_configuration = self.agents.AgentConfiguration(
            active_agent_id
        )

        interval_field = 'Interval'
        timeout_field = 'Timeout'
        idle_field = 'Idle'
        active_field = 'Active'
        realtime_field = 'RealTime'

        if self.api['version'] == 2:
            interval_field = 'interval_ms'
            timeout_field = 'timeout_ms'
            idle_field = idle_field.lower()
            active_field = active_field.lower()
            realtime_field = 'real_time'

        print('Agent Configuration:')
        print('\tAgent ID: {0}'.format(active_agent_id))
        print('\tLog Level: {0}'.format(agent_configuration.ConfigLogLevel))
        print('\tMinimum Disk Space:')
        print('\t\tBackup: {0} megabytes'.format(agent_configuration.MinimumBackupDiskSpaceMb))
        print('\t\tRestore: {0} megabytes'.format(agent_configuration.MinimumRestoreDiskSpaceMb))
        print('\t\tCleanup: {0} megabytes'.format(agent_configuration.MinimumCleanupDiskSpaceMb))
        print('\tRSE:')
        print('\t\tHost: {0}'.format(agent_configuration.RseHost))
        print('\t\tChannel: {0}'.format(agent_configuration.RseChannel))
        print('\t\tPolling Intervals:')
        polling_config = agent_configuration.RsePollingConfig
        print('\t\t\tInterval')
        print('\t\t\t\tIdle: {0} ms'.format(polling_config[interval_field][idle_field]))
        print('\t\t\t\tActive: {0} ms'.format(polling_config[interval_field][active_field]))
        print('\t\t\t\tReal-Time: {0} ms'.format(polling_config[interval_field][realtime_field]))
        print('\t\t\tTime-out')
        print('\t\t\t\tIdle: {0} ms'.format(polling_config[timeout_field][idle_field]))
        print('\t\t\t\tActive: {0} ms'.format(polling_config[timeout_field][active_field]))
        print('\t\t\t\tReal-Time: {0} ms'.format(polling_config[timeout_field][realtime_field]))
        print('\t\tHeart Beat Intervals:')
        heartbeat_config = agent_configuration.RseHeartbeatConfig
        print('\t\t\tInterval')
        print('\t\t\t\tIdle: {0} ms'.format(heartbeat_config[interval_field][idle_field]))
        print('\t\t\t\tActive: {0} ms'.format(heartbeat_config[interval_field][active_field]))
        print('\t\t\t\tReal-Time: {0} ms'.format(heartbeat_config[interval_field][realtime_field]))
        print('\t\t\tTime-out')
        print('\t\t\t\tIdle: {0} ms'.format(heartbeat_config[timeout_field][idle_field]))
        print('\t\t\t\tActive: {0} ms'.format(heartbeat_config[timeout_field][active_field]))
        print('\t\t\t\tReal-Time: {0} ms'.format(heartbeat_config[timeout_field][realtime_field]))
        print('\tVolumes:')
        for volume in agent_configuration.Volumes:
            for k, v in six.iteritems(volume):
                if k.lower() == 'password' and not show_password:
                    print('\t\t{0} = Hidden'.format(k))
                elif ((k.lower() == 'password' and show_password) or
                        k.lower() != 'password'):
                    if k == 'links':
                        for href_link in v:
                            print('\t\t\t{0} = {1}'.format(
                                href_link['rel'],
                                href_link['href']
                            ))
                    else:
                        print('\t\t{0} = "{1}"'.format(k, v))
        print('\n')

    def GetBackupIds(self, active_agent_id):
        info = []
        self.agents.GetAgentConfiguration(
            active_agent_id
        )

        agent_configuration = self.agents.AgentConfiguration(
            active_agent_id
        )

        for backup_id in agent_configuration.GetBackupIds():
            backup_name = agent_configuration.GetBackupNameFromId(
                backup_id
            )
            info.append({
                'id': backup_id,
                'name': backup_name
            })

        return info

    def doPrintLatestAgentActivity(self, active_agent_id, show_agent_id=True):
        activities = self.agents.GetAgentLatestActivity(active_agent_id)
        print('Agent ID: {0}'.format(active_agent_id))
        if len(activities):
            for activity in activities:
                print('\t{0} - {1}'.format(
                          activity['id'],
                          activity['name']
                      )
                )
                print('\t\tType: {0}'.format(activity['type']))
                print('\t\tState: {0}'.format(activity['state']))
                print('\t\tTime: {0}'.format(activity['time']))

        else:
            print('\tNo Activity to report')

        print('\n')

    def doMonitorAgent(self, active_agent_id):
        msg = 'Monitor Agent will periodically check agent acitivity and print out\n' \
              'messages until CTRL+C is pressed. Do you want to continue?'
        user_prompt_continue = cloudbackup.utils.menus.promptYesNoCancel(msg)
        if user_prompt_continue == 'Yes':
            msg_heartbeat =  'Show Agent Heart Beats?'
            user_prompt_heartbeat = cloudbackup.utils.menus.promptYesNoCancel(msg_heartbeat)

            show_heartbeat = False
            if user_prompt_heartbeat == 'Yes':
                show_heartbeat = True

            sleep_time = 0.25
            previous_marker = None
            last_event_id = None
            events = {}
            while True:
                try:
                    print('Checking for events after {0}'.format(last_event_id))
                    previous_marker = last_event_id
                    events, last_event_id = self.agents.GetAgentEventsSince(
                        active_agent_id,
                        last_event_id,
                        5,
                        events
                    )
                    if len(events):
                        for event_name, event_data in six.iteritems(events):
                            if event_name == 'heartbeats':
                                if show_heartbeat:
                                    for event_entry in event_data:
                                        print('\tHeart Beat - {0}'.format(
                                            event_entry['time']
                                        ))

                            else:
                                if len(event_data) > 1:
                                    print('\t{0}:'.format(event_name))
                                    for event_entry in event_data:
                                        print(event_entry)
                                else:
                                    print('\t{0}: {1}'.format(event_name, event_data))

                    # Pause
                    time.sleep(sleep_time)

                except KeyboardInterrupt:
                    break

    def RetrieveBackupReports(self, active_agent_id, config_id):
        while True:
            # Get the latest set of backups so the menu is always up-to-date
            all_backups = self.backup_engine.GetAllBackupsForConfiguration(
                active_agent_id,
                config_id
            )

            backup_config_menu = []
            for backup_entry in all_backups:
                backup_config_menu.append(
                    {
                        'index': len(backup_config_menu),
                        'text': '{0} - {2} - {1}'.format(
                            backup_entry['id'],
                            backup_entry['state'],
                            backup_entry['updated_at']
                        ),
                        'type': 'backup_id',
                        'backup_id': backup_entry['id']
                    }
                )
            backup_config_menu.append(
                {
                    'index': len(backup_config_menu),
                    'text': 'Return to previous menu',
                    'type': 'returnToPrevious'
                }
            )

            backup_config_selection = cloudbackup.utils.menus.promptSelection(
                backup_config_menu,
                'Select Backup'
            )
            if backup_config_selection['type'] == 'returnToPrevious':
                break

            elif backup_config_selection['type'] == 'backup_id':
                backup_report = self.backup_engine.GetBackupReport(
                    backup_config_selection['backup_id']
                )
                report_data = json.dumps(
                    backup_report,
                    sort_keys=True,
                    indent=4
                )
                print(report_data)
                cloudbackup.utils.menus.promptUserAnyKey()

    def RetrieveCleanupReports(self, active_agent_id):
        while True:
            # Get the latest set of backups so the menu is always up-to-date
            all_cleanups = self.backup_engine.GetAllCleanupsForConfiguration(
                active_agent_id
            )

            cleanup_config_menu = []
            for cleanup_entry in all_cleanups:
                cleanup_config_menu.append(
                    {
                        'index': len(cleanup_config_menu),
                        'text': '{0} - {2} - {1}'.format(
                            cleanup_entry['id'],
                            cleanup_entry['state'],
                            cleanup_entry['updated_at']
                        ),
                        'type': 'cleanup_id',
                        'cleanup_id': cleanup_entry['id']
                    }
                )
            cleanup_config_menu.append(
                {
                    'index': len(cleanup_config_menu),
                    'text': 'Return to previous menu',
                    'type': 'returnToPrevious'
                }
            )

            cleanup_config_selection = cloudbackup.utils.menus.promptSelection(
                cleanup_config_menu,
                'Select Cleanup'
            )
            if cleanup_config_selection['type'] == 'returnToPrevious':
                break

            elif cleanup_config_selection['type'] == 'cleanup_id':
                cleanup_report = self.backup_engine.GetCleanupReport(
                    cleanup_config_selection['cleanup_id']
                )
                report_data = json.dumps(
                    cleanup_report,
                    sort_keys=True,
                    indent=4
                )
                print(report_data)
                cloudbackup.utils.menus.promptUserAnyKey()

    def EnableDisableSpecificAgentConfiguration(self, active_agent_id, config_id):
        while True:
            try:
                # update the agent configuration
                self.agents.GetAgentConfiguration(
                    active_agent_id
                )
                # access the backup configuration
                backup_config = self.agents.AgentConfiguration(
                    active_agent_id
                ).GetBackupConfigurationById(
                    config_id
                )
            except:
                backup_config = None

            if backup_config is None:
                print('Backup Config no longer accessible.')
                return

            backup_config_enabled = False
            if self.api['version'] == 1:
                backup_config_enabled = backup_config['IsEnabled']
            else:
                backup_config_enabled = backup_config['enabled']

            current_state = 'Enabled' if backup_config_enabled else 'Disabled'
            config_state_entry = {
                'index': 0,
                'text': 'Disable Configuration',
                'type': 'stateChange',
                'value': False
            }
            if backup_config_enabled:
                config_state_entry['text'] = 'Disable Configuration'
                config_state_entry['value'] = False

            else:
                config_state_entry['text'] = 'Enable Configuration'
                config_state_entry['value'] = True

            enable_disable_menu = [
                config_state_entry,
                { 'index': 1, 'text': 'Update Configuration State', 'type': 'updateState' },
                { 'index': 2, 'text': 'Return to previous menu', 'type': 'returnToPrevious' }
            ]

            print('Current Configuration State: {0}'.format(current_state))
            selection = cloudbackup.utils.menus.promptSelection(
                enable_disable_menu,
                'Select Action'
            )

            if selection['type'] == 'returnToPrevious':
                return

            elif selection['type'] == 'updateState':
                # nothing to do, we'll update automatically on next loop
                # this just makes it so the user doesn't get an input error
                continue

            elif selection['type'] == 'stateChange':
                if self.backup_engine.EnableDisableBackupConfiguration(
                    active_agent_id,
                    config_id,
                    selection['value']
                ):
                    print('Configuration status updated')

                else:
                    print('Failed to update configuration status')

    def DeleteBackupConfiguration(self, active_agent_id, config_id):
        verify_delete = cloudbackup.utils.menus.promptYesNoCancel(
            'Confirm Delete Configuration {0} - {1}'.format(
                config_id,
                config_name
            )
        )
        if verify_delete == 'Yes':
            print('Deleting configuration...')
            if self.backup_engine.DeleteBackupConfiguration(
                    config_id):
                # Config no longer exists, so return to previous menu
                return
            else:
                print('Failed to delete configuration. See log for details')

        else:
            print('Canceling deletion of configuration.')

    def WorkOnSpecificAgentConfiguration(self, active_agent_id, config_id, config_name):
        specific_config_menu = [
            { 'index': 0, 'text': 'Run', 'type': 'actionRun' },
            { 'index': 1, 'text': 'Show', 'type': 'actionShow' },
            { 'index': 2, 'text': 'Check Status', 'type': 'actionCheckStatus'},
            { 'index': 3, 'text': 'Enable/Disable Configuration', 'type': 'actionEnableDisable'},
            { 'index': 4, 'text': 'Get Backup Reports', 'type': 'actionGetBackupReports'},
            { 'index': 5, 'text': 'Return to previous menu', 'type': 'returnToPrevious' },
            { 'index': 99, 'text': 'Delete', 'type': 'actionDelete' }
        ]

        while True:
            print('Agent ID: {0}'.format(active_agent_id))
            print('\tBackup Configuration ID: {0}'.format(config_id))
            print('\tBackup Configuration Name:: {0}'.format(config_name))

            if active_agent_id in self.snapshot_ids.keys():
                print('\tRunning Backup Snapshot ID: {0}'.format(self.snapshot_ids[active_agent_id]))

            selection = cloudbackup.utils.menus.promptSelection(
                specific_config_menu,
                'Select Action'
            )

            if selection['type'] == 'returnToPrevious':
                return

            elif selection['type'] == 'actionRun':
                if not active_agent_id in self.snapshot_ids.keys():
                    print('Starting Backup...')
                    backup_id = self.backup_engine.StartBackup(config_id)
                    print('\tBackup Id: {0}'.format(backup_id))
                else:
                    print('A Backup is already running.')

            elif selection['type'] == 'actionShow':
                self.doPrintBackupConfigurationDetails(
                    active_agent_id,
                    config_id,
                    config_name
                )

            elif selection['type'] == 'actionCheckStatus':
                snapshot_id = None
                if not active_agent_id in self.snapshot_ids.keys():
                    print('No known Backup is running.')
                    user_provides_snapshot_id = cloudbackup.utils.menus.promptYesNoCancel(
                        'Do you know of a Snapshot ID for this agent to check on?'
                    )
                    if user_provides_snapshot_id == 'Yes':
                        snapshot_id = cloudbackup.utils.menus.promptUserInputString(
                            'Snapshot ID',
                            ''
                        )
                else:
                    snapshot_id = self.snapshot_ids['active_agent_id']

                if not snapshot_id is None:
                    snapshot_state = None
                    try:
                        if self.api['version'] == 1:
                            snapshot_state = self.backup_engine.GetBackupProgressV1(
                                snapshot_id
                            )

                        else:
                            snapshot_state = self.backup_engine.GetBackupProgressV2

                        if not active_agent_id in self.snapshot_ids:
                            self.snapshot_ids[active_agent_id] = snapshot_id

                        state = ''
                        stop_states = []
                        if self.api['version'] == 1:
                            state = 'CurrentState'
                            stop_states = ['Completed', 'Skipped', 'Missed', 'Stopped', 'Failed', 'CompletedWithErrors']
                        else:
                            state = 'state'
                            stop_states = ['completed', 'skipped', 'missed', 'stopped', 'failed', 'completed_with_errors']

                        if snapshot_state[state] in stop_states:
                            del self.snapshot_ids[active_agent_id]

                    except RuntimeError as ex:
                        print('Error retrieving snapshot state: {0}'.format(ex))

            elif selection['type'] == 'actionGetBackupReports':
                self.RetrieveBackupReports(
                    active_agent_id,
                    config_id
                )

            elif selection['type'] == 'actionEnableDisable':
                self.EnableDisableSpecificAgentConfiguration(
                    active_agent_id,
                    config_id
                )

            elif selection['type'] == 'actionDelete':
                self.DeleteBackupConfiguration(
                    active_agent_id,
                    config_id
                )

    def WorkOnAgentConfiguration(self, active_agent_id):
        while True:
            print('Agent ID: {0}'.format(active_agent_id))

            backup_configuration_ids = self.GetBackupIds(
                active_agent_id
            )

            agent_configuration_menu = [
                {
                    'index': 0,
                    'text': 'Show Agent Global Configuration',
                    'type': 'showAgentGlobalConfiguration'
                }
            ]

            for info in backup_configuration_ids:
                backup_id = info['id']
                backup_name = info['name']

                agent_configuration_menu.append({
                    'index': len(agent_configuration_menu),
                    'text': '{0} - {1}'.format(
                        backup_id,
                        backup_name
                    ),
                    'type': 'configuration',
                    'id': backup_id,
                    'name': backup_name
                })

            agent_configuration_menu.append({
                'index': len(agent_configuration_menu),
                'text': 'Add New Backup Configuration',
                'type': 'addConfiguration'
            })

            agent_configuration_menu.append({
                'index': len(agent_configuration_menu),
                'text': 'Return to previous menu',
                'type': 'returnToPrevious'
            })

            selection = cloudbackup.utils.menus.promptSelection(
                agent_configuration_menu,
                'Select Action'
            )

            if selection['type'] == 'returnToPrevious':
                return

            elif selection['type'] == 'addConfiguration':
                self.doCreateBackupConfiguration(
                    active_agent_id
                )

            elif selection['type'] == 'showAgentGlobalConfiguration':
                self.doPrintAgentGlobalConfiguration(
                    active_agent_id
                )

            elif selection['type'] == 'configuration':
                self.WorkOnSpecificAgentConfiguration(
                    active_agent_id,
                    selection['id'],
                    selection['name']
                )

    def WorkOnAgentLogFiles(self, active_agent_id):
        while True:
            print('Agent ID: {0}'.format(active_agent_id))

            available_log_files = self.agents.GetExistingAgentLogFiles(
                active_agent_id
            )

            agent_logfile_menu = []
            for log_file_entry in available_log_files:
                entry = {
                    'index': len(agent_logfile_menu),
                    'type': 'logfile',
                    'text': 'Log File[{0}] - {1}'.format(
                            log_file_entry['date'],
                            log_file_entry['status']
                        ),
                    'value': log_file_entry
                }
                agent_logfile_menu.append(entry)

            agent_logfile_menu.append(
                {
                    'index': len(agent_logfile_menu),
                    'type': 'actionRequestLogFile',
                    'text': 'Request New Log File',
                    'value': None
                }
            )
            agent_logfile_menu.append(
                {
                    'index': len(agent_logfile_menu),
                    'type': 'actionUpdate',
                    'text': 'Update Listing',
                    'value': None
                }
            )
            agent_logfile_menu.append(
                {
                    'index': len(agent_logfile_menu),
                    'type': 'returnToPrevious',
                    'text': 'Return to previous menu',
                    'value': None
                }
            )

            selection = cloudbackup.utils.menus.promptSelection(
                agent_logfile_menu,
                'Select Action'
            )

            if selection['type'] == 'actionUpdate':
                continue

            elif selection['type'] == 'returnToPrevious':
                return

            elif selection['type'] == 'logfile':
                if selection['value']['status'] in ('Finished', 'completed'):
                    download_output_filename = cloudbackup.utils.menus.promptUserInputString(
                        'Output Filename',
                        ''
                    )
                    if download_output_filename is not None:
                        print('Downloading file to {0}'.format(download_output_filename))
                        successful_download = self.agents.DownloadAgentLogFile(
                            selection['value'],
                            download_output_filename
                        )
                        if not successful_download:
                            print('Failed to download log file.')
                else:
                    print('File not ready for download')

            elif selection['type'] == 'actionRequestLogFile':
                log_req_result = self.agents.GetAgentLogFile(active_agent_id)
                if log_req_result is None:
                    print('Failed to request a new agent log file upload')

    def WorkOnAgentLog(self, active_agent_id):
        agent_log_menu = [
            { 'index': 0, 'text': 'Get Log Level', 'type': 'actionGetLogLevel' },
            { 'index': 1, 'text': 'Set Log Level', 'type': 'actionSetLogLevel' },
            { 'index': 2, 'text': 'Log Files', 'type': 'actionLogFiles' },
            { 'index': 3, 'text': 'Return to previous menu', 'type': 'returnToPrevious' }
        ]

        agent_log_level_menu = [
            { 'index': 0, 'text': 'All Levels', 'type': 'loglevel', 'value': 'All' },
            { 'index': 1, 'text': 'Trace', 'type': 'loglevel', 'value': 'Trace' },
            { 'index': 2, 'text': 'Debug', 'type': 'loglevel', 'value': 'Debug' },
            { 'index': 3, 'text': 'Info', 'type': 'loglevel', 'value': 'Info' },
            { 'index': 4, 'text': 'Warn', 'type': 'loglevel', 'value': 'Warn' },
            { 'index': 5, 'text': 'Error', 'type': 'loglevel', 'value': 'Error' },
            { 'index': 6, 'text': 'Fatal', 'type': 'loglevel', 'value': 'Fatal' },
            { 'index': 7, 'text': 'Cancel', 'type': 'cancel' }
        ]

        while True:
            print('Agent ID: {0}'.format(active_agent_id))

            selection = cloudbackup.utils.menus.promptSelection(
                agent_log_menu,
                'Selection Action'
            )

            if selection['type'] == 'returnToPrevious':
                return

            elif selection['type'] == 'actionGetLogLevel':
                current_log_level = self.agents.loglevel.GetLogLevel(
                    active_agent_id
                )
                print('\tActive Log Level: {0}'.format(current_log_level))

            elif selection['type'] == 'actionSetLogLevel':
                log_level_selection = cloudbackup.utils.menus.promptSelection(
                    agent_log_level_menu,
                    'Select Log Level'
                )

                if log_level_selection['type'] == 'cancel':
                    pass

                elif log_level_selection['type'] == 'loglevel':
                    print('Attempting to set log level to {0}'.format(
                        log_level_selection['text']
                    ))
                    if not self.agents.loglevel.SetLogLevel(
                            active_agent_id,
                            log_level_selection['value']
                            ):
                        self.log.debug('Failed to set log level')
                        print('Failed to set log level')

            elif selection['type'] == 'actionLogFiles':
                self.WorkOnAgentLogFiles(active_agent_id)

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
            woke_agent = False
            should_wake_agent = cloudbackup.utils.menus.promptYesNoCancel(
                'Wake agent?'
                ''
            )
            if should_wake_agent == 'Yes':
                print('Attempting to wake the agent...')
                self.agents.GetAgentConfiguration(
                    active_agent_id
                )

                agent_configuration = self.agents.AgentConfiguration(
                    active_agent_id
                )
                self.rse = cloudbackup.client.rse.Rse(
                    'cloudbackup-sdk-shell',
                    '1.0',
                    self.auth_engine,
                    self.agents,
                    agent_configuration.RseChannel,
                    apihost=self.api['uri'],
                    api_version=self.api['version'],
                    project_id=self.auth_engine.AuthTenantId
                )
                self.agents.WakeSpecificAgent(
                    active_agent_id,
                    self.rse,
                    1000,
                    keep_agent_awake=True
                )
                woke_agent = True

            continue_specific_agent_config = True
            agent_details = self.agents.AgentDetails(active_agent_id)
            while continue_specific_agent_config:
                print('Agent Details:')
                print('\tAgent ID: {0}'.format(agent_details.agent_id))
                print('\tAgent Version: {0}'.format(agent_details.AgentVersion))

                # menu
                agent_detail_menu = [
                    { 'index': 1, 'text': 'Show Details', 'type': 'details' },
                    { 'index': 2, 'text': 'Log Configuration', 'type': 'actionLog' },
                    { 'index': 3, 'text': 'Access Backup Configurations', 'type': 'configuration' },
                    { 'index': 4, 'text': 'Check agent activity', 'type': 'actionCheckActivity' },
                    { 'index': 5, 'text': 'Monitor Agent Events', 'type': 'actionMonitorAgent' },
                    { 'index': 6, 'text': 'Get Cleanup Reports', 'type': 'actionGetCleanupReports'},
                    { 'index': 7, 'text': 'Return to previous menu', 'type': 'returnToPrevious' }
                ]

                selection = cloudbackup.utils.menus.promptSelection(
                    agent_detail_menu,
                    'Selection Action'
                )
                if selection['type'] == 'returnToPrevious':
                    continue_specific_agent_config = False

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

                elif selection['type'] == 'actionLog':
                    self.WorkOnAgentLog(active_agent_id)

                elif selection['type'] == 'configuration':
                    self.WorkOnAgentConfiguration(active_agent_id)

                elif selection['type'] == 'actionCheckActivity':
                    self.doPrintLatestAgentActivity(active_agent_id)

                elif selection['type'] == 'actionMonitorAgent':
                    self.doMonitorAgent(active_agent_id)

                elif selection['type'] == 'actionGetCleanupReports':
                    self.RetrieveCleanupReports(active_agent_id)

            if woke_agent:
                # stop our thread that is keeping the agent alive
                print('Allowing the agent to throttle down...')
                self.agents.StopKeepAgentWake(active_agent_id)

    def doShell(self):
        while True:
            # Note: there is presently no paging in this menu selection
            agent_selection = self.GetAgentIdFromUser()
            if agent_selection['type'] == 'EXIT':
                return 0

            else:
                self.WorkOnAgent(agent_selection['text'])

