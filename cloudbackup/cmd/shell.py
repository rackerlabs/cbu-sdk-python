#!/usr/bin/python
from __future__ import print_function

import argparse
import json
import logging
import random
import sys

import six

import cloudbackup.client.agents
import cloudbackup.client.auth
import cloudbackup.client.backup
import cloudbackup.utils.menus
from cloudbackup.utils import tz

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
        self.api['version'] = self.auth_engine.GetCloudBackupApiVersion(
            self.datacenter,
            self.use_servicenet
        )
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

    @staticmethod
    def doPromptBackConfigurationName(user_aborted=False):
        name = None
        if not user_aborted:
            name = cloudbackup.utils.menus.promptUserInputString(
                'Backup Configuration Name',
                '',
            )
        return name

    @staticmethod
    def doPromptFrequency(api_version, user_aborted=False):
        data = {
            'frequency': None,
            'dayOfWeek': None,
            'StartTime': {
                'hour': None,
                'minute': None,
                'amOrPm': None,
                'timeZone': None
            },
            'interval': None
        }

        def promptBaseRate():
            base_rate_menu = [
                { 'index': 0, 'text': 'Manually', 'type': 'frequency' },
                { 'index': 1, 'text': 'Hourly', 'type': 'frequency' },
                { 'index': 2, 'text': 'Daily', 'type': 'frequency' },
                { 'index': 3, 'text': 'Weekly', 'type': 'frequency' },
                { 'index': 4, 'text': 'Return to previous menu', 'type': 'returnToPrevious' }
            ]
            base = cloudbackup.utils.menus.promptSelection(
                base_rate_menu,
                'Select Frequency'
            )

            if base['type'] == 'frequency':
                return base['text']

            elif base['type'] == 'returnToPrevious':
                print('Aborting')
                user_aborted = True
                return None

        def promptWeekDay():
            weekday_menu = [
                { 'index': 0, 'text': 'Sunday', 'type': 'day' },
                { 'index': 1, 'text': 'Monday', 'type': 'day' },
                { 'index': 2, 'text': 'Tuesday', 'type': 'day' },
                { 'index': 3, 'text': 'Wednesday', 'type': 'day' },
                { 'index': 4, 'text': 'Thursday', 'type': 'day' },
                { 'index': 5, 'text': 'Friday', 'type': 'day' },
                { 'index': 6, 'text': 'Saturday', 'type': 'day' },
                { 'index': 7, 'text': 'Return to previous menu', 'type': 'returnToPrevious' }
            ]
            weekday = cloudbackup.utils.menus.promptSelection(
                weekday_menu,
                'Select Day of Week'
            )

            if weekday['type'] == 'day':
                return weekday['text']

            elif weekday['type'] == 'returnToPrevious':
                print('Aborting')
                user_aborted = True
                return None

        def promptStartTime():
            data['StartTime']['hour'] = cloudbackup.utils.menus.promptUserInputNumber(
                'Hour',
                '',
                0,
                13,
                show_range=True
            )
            if data['StartTime']['hour'] is None:
                print('Aborting')
                user_aborted = True

            else:
                data['StartTime']['minute'] = cloudbackup.utils.menus.promptUserInputNumber(
                    'Minute',
                    '',
                    0,
                    61,
                    show_range=True
                )
                if data['StartTime']['minute'] is None:
                    print('Aborting')
                    user_aborted = True

                else:
                    amOrPm_menu = [
                        { 'index': 0, 'text': 'AM', 'type': 'period' },
                        { 'index': 1, 'text': 'PM', 'type': 'period' },
                        { 'index': 2, 'text': 'Return to previous menu', 'type': 'returnToPrevious' }
                    ]
                    amPmSelection = cloudbackup.utils.menus.promptSelection(
                        amOrPm_menu,
                        'Select'
                    )

                    if amPmSelection['type'] == 'returnToPrevious':
                        print('Aborting')
                        user_aborted = True

                    else:
                        data['StartTime']['amOrPm'] = amPmSelection['text']

                        valid_keys = []
                        if api_version == 1:
                            valid_keys = tz.get_v1_timezone_name_list()
                        elif api_version == 2:
                            valid_keys = tz.get_v2_timezone_name_list()
                        else:
                            print('Unknown Cloud Backup API Version. Assuming V2 or later...')
                            valid_keys = tz.get_v2_timezone_name_list()

                        tz_menu = [
                        ]
                        for tz_name in valid_keys:
                            tz_menu.append({
                                'index': len(tz_menu),
                                'text': tz_name,
                                'type': 'timezone_name'
                            })
                        tz_menu.append({
                            'index': len(tz_menu),
                            'text': 'Cancel',
                            'type': 'returnToPrevious'
                        })

                        tz_selection = cloudbackup.utils.menus.promptSelection(
                            tz_menu,
                            'Time Zone Selection'
                        )

                        if tz_selection['type'] == 'returnToPrevious':
                            print('Aborting')
                            user_aborted = True

                        elif tz_selection['type'] == 'timezone_name':
                            data['StartTime']['timeZone'] = tz_selection['text']

        if not user_aborted:
            data['frequency'] = promptBaseRate()

        if not user_aborted:
            if data['frequency'] == 'Weekly':
                data['dayOfWeek'] = promptWeekDay()

            if data['frequency'] in ('Weekly', 'Daily'):
                promptStartTime()

            if data['frequency'] == 'Hourly':
                data['interval'] = cloudbackup.utils.menus.promptUserInputNumber(
                    'Hourly Interval',
                    '',
                    0,
                    24,
                    show_range=True
                )

                if data['interval'] is None:
                    user_aborted = True
            else:
                # TODO: Prompt for how often to run non-hourly intervals
                data['interval'] = 1

        if not user_aborted:
            return data
        else:
            return None

    @staticmethod
    def doPromptRetention(user_aborted=False):
        retention = None

        if not user_aborted:
            retention_menu = [
                { 'index': 0, 'text': 'Indefinite', 'type': 'retention', 'r': 0 },
                { 'index': 1, 'text': '30 Day', 'type': 'retention', 'r': 30 },
                { 'index': 2, 'text': '60 Day', 'type': 'retention', 'r': 60 },
                { 'index': 3, 'text': 'Return to previous menu', 'type': 'returnToPrevious' }
            ]
            selection = cloudbackup.utils.menus.promptSelection(
                retention_menu,
                'Select Retention'
            )

            if selection['type'] == 'retention':
                retention = selection['r']

            elif selection['type'] == 'returnToPrevious':
                print('Aborting')
                user_aborted = True
                retention = None

        return retention

    @staticmethod
    def doPromptNotifications(user_aborted=False):
        notification_data = None

        if not user_aborted:
            notification_data = {
                'addresses': [],
                'onSuccess': False,
                'onFailure': True
            }

            while True:
                notification_menu = [
                ]
                li = 0
                for address in notification_data['addresses']:
                    notification_menu.append({
                        'index': len(notification_menu),
                        'text': address,
                        'type': 'address',
                        'li': li
                    })
                    li = li + 1
                notification_menu.append({
                    'index': len(notification_menu),
                    'text': 'Add E-mail Address',
                    'type': 'addAddress'
                })
                notification_menu.append({
                    'index': len(notification_menu),
                    'text': 'Save',
                    'type': 'save'
                })
                notification_menu.append({
                    'index': len(notification_menu),
                    'text': 'Cancel',
                    'type': 'returnToPrevious'
                })

                selection = cloudbackup.utils.menus.promptSelection(
                    notification_menu,
                    'Select Action'
                )

                if selection['type'] == 'returnToPrevious':
                    print('Aborting')
                    notification_data = None
                    user_aborted = True
                    break

                elif selection['type'] == 'save':
                    if not len(notification_data['addresses']):
                        print('No e-mail addresses provided.')
                        print('There must be at least one (1) e-mail address.')
                    else:
                        break

                elif selection['type'] == 'addAddress':
                    addressToAdd = cloudbackup.utils.menus.promptUserInputString(
                        'E-mail Address',
                        '',
                    )
                    if not addressToAdd is None:
                        notification_data['addresses'].append(addressToAdd)

                elif selection['type'] == 'address':
                    removeAddress = cloudbackup.utils.menus.promptYesNoCancel(
                        'Remove {0} from the list?'.format(selection['text']),
                        ''
                    )
                    if removeAddress == 'Yes':
                        try:
                            list_index = selection['li']
                            if notification_data['addresses'][list_index] == selection['text']:
                                del notification_data['addresses'][list_index]
                        except:
                            print('Error while removing E-mail Address from list')

        if not user_aborted:
            notifySuccess = cloudbackup.utils.menus.promptYesNoCancel(
                'Notify on successful events?',
                ''
            )
            if notifySuccess == 'Yes':
                notification_data['onSuccess'] = True

        return notification_data

    @staticmethod
    def doPromptFilesAndFolders(user_aborted=True, inclusion=False):
        files_and_folders = None

        if not user_aborted:
            files_and_folders = []
            while True:
                files_and_folders_menu = [
                ]
                li = 0
                for fileOrFolder in files_and_folders:
                    item_name, item_type = fileOrFolder
                    files_and_folders_menu.append({
                        'index': len(files_and_folders_menu),
                        'text': '{0} - {1}'.format(item_name, item_type),
                        'type': 'fileOrFolder',
                        'li': li
                    })
                    li = li + 1

                files_and_folders_menu.append({
                    'index': len(files_and_folders_menu),
                    'text': 'Add File',
                    'type': 'addFile'
                })
                files_and_folders_menu.append({
                    'index': len(files_and_folders_menu),
                    'text': 'Add Folder',
                    'type': 'addFolder'
                })
                files_and_folders_menu.append({
                    'index': len(files_and_folders_menu),
                    'text': 'Save',
                    'type': 'save'
                })
                files_and_folders_menu.append({
                    'index': len(files_and_folders_menu),
                    'text': 'Cancel',
                    'type': 'returnToPrevious'
                })

                menu_prompt = '{0} Selection'.format(
                    'Inclusion' if inclusion else 'Exclusion'
                )

                selection = cloudbackup.utils.menus.promptSelection(
                    files_and_folders_menu,
                    menu_prompt
                )

                if selection['type'] == 'returnToPrevious':
                    print('Aborting')
                    files_and_folders = None
                    user_aborted = True
                    break

                elif selection['type'] == 'save':
                    if inclusion and not len(files_and_folders):
                        print('There must be at least 1 file or folder specified for inclusion')
                    else:
                        break

                elif selection['type'] == 'addFile':
                    fileOrFolderToAdd = cloudbackup.utils.menus.promptUserInputString(
                        'File Path',
                        '',
                    )
                    if not fileOrFolderToAdd is None:
                        files_and_folders.append((fileOrFolderToAdd, 'file'))

                elif selection['type'] == 'addFolder':
                    fileOrFolderToAdd = cloudbackup.utils.menus.promptUserInputString(
                        'Folder Path',
                        '',
                    )
                    if not fileOrFolderToAdd is None:
                        files_and_folders.append((fileOrFolderToAdd, 'folder'))

                elif selection['type'] == 'fileOrFolder':
                    removeFileOrFolder = cloudbackup.utils.menus.promptYesNoCancel(
                        'Remove {0} from the list?'.format(selection['text']),
                        ''
                    )
                    if removeFileOrFolder == 'Yes':
                        try:
                            list_index = selection['li']
                            if files_and_folders[list_index][0] == selection['text']:
                                del files_and_folders[list_index]
                        except:
                            print('Error while removing File or Folder Path from list')

        return files_and_folders

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
        print(type(backup_config))
        print(dir(backup_config))
        assert(hasattr(backup_config, 'dict_source'))

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

        if config_data['schedule']['start-time']['hour'] is not None:
            # Convert the Hour to 24-hour format
            config_data['schedule']['start-time']['hour'] = (
                config_data['schedule']['start-time']['hour']
                - 1
            )
            if config_data['schedule']['start-time']['am-pm'] == 'PM':
                # Convert from AM to PM
                config_data['schedule']['start-time']['hour'] = (
                    config_data['schedule']['start-time']['hour']
                    + 12
                )

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

        prompted_config_data['name'] = CloudBackupApiShell.doPromptBackConfigurationName(
            user_aborted
        )
        user_aborted = check_user_aborted(prompted_config_data['name'])

        frequency_data = CloudBackupApiShell.doPromptFrequency(
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

        prompted_config_data['retention'] = CloudBackupApiShell.doPromptRetention(
            user_aborted
        )

        notification_data = CloudBackupApiShell.doPromptNotifications(
            user_aborted
        )
        user_aborted = check_user_aborted(notification_data)
        if not user_aborted:
            prompted_config_data['notifications']['e-mail-addresses'] = notification_data['addresses']
            prompted_config_data['notifications']['success'] = notification_data['onSuccess']
            prompted_config_data['notifications']['failure'] = notification_data['onFailure']

        inclusion_data = CloudBackupApiShell.doPromptFilesAndFolders(
            user_aborted,
            inclusion=True
        )
        user_aborted = check_user_aborted(inclusion_data)
        if not user_aborted:
            prompted_config_data['paths']['inclusions'] = inclusion_data

        exclusion_data = CloudBackupApiShell.doPromptFilesAndFolders(
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
        print('\t\tIncluded Files and Folders:')
        for inclusion in backup_config['Inclusions']:
            print('\t\t\tType: {0}'.format(inclusion['Type']))
            print('\t\t\tPattern: {0}'.format(inclusion['Pattern']))
            print('\t\t\tModule: {0}'.format(inclusion['Module']))
            print('\t\t\tArgs: {0}'.format(inclusion['Args']))
        print('\t\tExcluded Files and Folders:')
        for exclusion in backup_config['Exclusions']:
            print('\t\t\tType: {0}'.format(exclusion['Type']))
            print('\t\t\tPattern: {0}'.format(exclusion['Pattern']))
            print('\t\t\tModule: {0}'.format(exclusion['Module']))
            print('\t\t\tArgs: {0}'.format(exclusion['Args']))
        print('\n')

    def doPrintBackupConfigurationV2Details(self, active_agent_id, backup_config):
        print('Agent Configuration:')
        print('\tAgent ID: {0}'.format(active_agent_id))
        print('\t\t ID: {0}'.format(backup_config['id']))
        print('\t\t Name: {0}'.format(backup_config['name']))
        print('\t\t Config: {0}'.format(backup_config))
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
                self.doPrintBackupConfigurationDetails(
                    active_agent_id,
                    selection['id'],
                    selection['name']
                )


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
                    self.WorkOnAgentConfiguration(active_agent_id)

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
