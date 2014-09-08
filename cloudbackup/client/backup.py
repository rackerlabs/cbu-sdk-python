"""
Rackspace Cloud Backup Configuration Support
"""
from __future__ import print_function

import json
import logging
import requests
import time
from time import sleep
import types
import uuid

from cloudbackup.common.command import Command
from cloudbackup.utils import tz


class BackupConfiguration(object):
    """
    Python Class to wrap a backup configuration
    """

    @staticmethod
    def UniqueBackupName():
        """
        Return a unique backup name. It may not have any useful user meaning, but it will be unique.
        """
        return str(uuid.uuid1())

    @staticmethod
    def CreateBackupConfigurationTemplate():
        """
        Return a dictionary with the data for creating the backup configuration with sane default values

        Note: By default, it is configured as a Manual Backup with 30 day retention
        Warning: The name and machine agent id need to be added
        """
        backupconfig_template = {}
        backupconfig_template['BackupConfigurationId'] = None
        backupconfig_template['BackupConfigurationName'] = None
        backupconfig_template['MachineAgentId'] = None
        backupconfig_template['IsActive'] = False
        backupconfig_template['VersionRetention'] = 30
        backupconfig_template['BackupConfigurationScheduled'] = None
        backupconfig_template['MissedBackupActionId'] = 1
        backupconfig_template['Frequency'] = 'Manually'
        backupconfig_template['StartTimeHour'] = None
        backupconfig_template['StartTimeMinute'] = None
        backupconfig_template['StartTimeAmPm'] = None
        backupconfig_template['DayOfWeekId'] = None
        backupconfig_template['HourInterval'] = None
        backupconfig_template['TimeZoneId'] = tz.get_timezone()
        backupconfig_template['NotifyRecipients'] = ''
        backupconfig_template['NotifySuccess'] = False
        backupconfig_template['NotifyFailure'] = False
        backupconfig_template['Inclusions'] = []
        backupconfig_template['Exclusions'] = []
        return backupconfig_template

    @staticmethod
    def CreateNamedBackupConfiguration(name, machine_agent_id):
        """
        Return a diction with the data for creating the backup confiugration with sane default values.
            name - the name of the backup configuration
            machine_agent_id - the machine agent id for the agent performing the backup

        Note: By default, it configures a Manual Backup with 30 day retention.
        """
        backup_config = BackupConfiguration.CreateBackupConfigurationTemplate()
        backup_config['BackupConfigurationName'] = name
        backup_config['MachineAgentId'] = machine_agent_id
        return backup_config

    def __init__(self):
        """
        Initialize the BackupConfiguration instance with a copy of the template data
        """
        self.log = logging.getLogger(__name__)
        self.backup_config = BackupConfiguration.CreateBackupConfigurationTemplate()
        self.from_dict = None

    @classmethod
    def from_dict(cls, config, source):
        """
        Create a BackupConfiguration from an existing dictionary

        Parameters:
            config - configuration dictionary to base on
            source - source the dictionary is derived from

        The source parameter is provided as the agent configuration details that contain a backup configuration
        specify it differently than the backup configuration details do. The parameter has 3 possible values:
            None
            'agent-configuration'
            'backup-configuration'

        If source is None then it will default to 'agent-configuration'.
        """
        if source not in (None, 'agent-configuration', 'backup-configuration'):
            raise ValueError('configuration source data is not valid')

        rbc = BackupConfiguration()
        try:
            rbc.dict_source = source
            rbc.from_dict = config
            rbc.backup_config = BackupConfiguration.CreateBackupConfigurationTemplate()

            keys_to_copy = []

            if source in (None, 'agent-configuration'):
                # Guarantee we know where the data come from, even if not specified
                rbc.source = 'agent-configuration'

                rbc.Active = config['IsActive']
                rbc.DayOfWeekId = config['DayOfWeekId']
                rbc.Frequency = config['Frequency']
                rbc.HourInterval = config['HourInterval']
                rbc.MachineAgentId = config['MachineAgentId']
                rbc.MissedBackupActionId = config['MissedBackupActionId']
                rbc.NotifyFailure = config['NotifyFailure']
                rbc.NotifyRecipients = config['NotifyRecipients']
                rbc.NotifySuccess = config['NotifySuccess']
                rbc.Scheduled = config['BackupConfigurationScheduled']
                rbc.StartTimeAmPm = config['StartTimeAmPm']
                rbc.StartTimeHour = config['StartTimeHour']
                rbc.StartTimeMinute = config['StartTimeMinute']
                rbc.TimeZoneId = config['TimeZoneId']
                rbc.VersionRetention = config['VersionRetention']

                keys_to_copy = ['BackupConfigurationName', 'Exclusions', 'Inclusions']

            elif source == 'backup-configuration':
                rbc.Active = rbc.from_dict['IsActive']
                rbc.ConfigurationId = rbc.from_dict['BackupConfigurationId']
                rbc.ConfigurationName = rbc.from_dict['BackupConfigurationName']
                rbc.DayOfWeekId = rbc.from_dict['DayOfWeekId']
                rbc.Frequency = rbc.from_dict['Frequency']
                rbc.HourInterval = rbc.from_dict['HourInterval']
                rbc.MachineAgentId = rbc.from_dict['MachineAgentId']
                rbc.MachineName = rbc.from_dict['MachineName']
                rbc.MissedBackupActionId = config['MissedBackupActionId']
                rbc.NotifyFailure = rbc.from_dict['NotifyFailure']
                rbc.NotifyRecipients = rbc.from_dict['NotifyRecipients']
                rbc.NotifySuccess = rbc.from_dict['NotifySuccess']

                if len(rbc.from_dict['StartTimeAmPm']):
                    rbc.StartTimeAmPm = rbc.from_dict['StartTimeAmPm']

                rbc.StartTimeHour = rbc.from_dict['StartTimeHour']
                rbc.StartTimeMinute = rbc.from_dict['StartTimeMinute']
                rbc.TimeZoneId = rbc.from_dict['TimeZoneId']
                rbc.VersionRetention = rbc.from_dict['VersionRetention']

                keys_to_copy = ['BackupConfigurationScheduleId',
                                'BackupPostscript',
                                'BackupPrescript',
                                'Datacenter',
                                'EncryptionKey',
                                'Exclusions',
                                'Flavor',
                                'Inclusions',
                                'IsDeleted',
                                'IsEncrypted',
                                'LastRunBackupReportId',
                                'LastRunTime',
                                'NextScheduledRunTime'
                                ]
            for key in keys_to_copy:
                rbc.backup_config[key] = rbc.from_dict[key]

        except LookupError as ex:
            raise TypeError('config does not contain the correct dictionary entries - {0:} : {1:}'.format(ex, config))

        return rbc

    @property
    def to_dict(self):
        """
        Return the object as a dictionary
        """
        return self.backup_config

    @property
    def to_creation_dict(self):
        """
        Return the object as a dictionary in a format acceptable for submitting as a new backup configuration to the Rackspace Cloud Backup API
        """
        # create backup takes a copy without the BackupConfigurationSchedule entry
        rbc = self.backup_config

        keys_to_remove = []

        if self.dict_source == 'agent-configuration':
            keys_to_remove = ['BackupConfigurationId',
                              'BackupConfigurationScheduled']

        elif self.dict_source == 'backup-configuration':
            keys_to_remove = ['LastRunBackupReportId',
                              'LastRunTime']

        else:
            raise ValueError('Unknown backup configuration source. Unable to clean the dictionary')

        for key in keys_to_remove:
            del rbc[key]

        return rbc

    @property
    def to_update_dict(self):
        """
        Return the object as a dictionary in a format acceptable for submitting as a new backup configuration to the Rackspace Cloud Backup API
        """
        # create backup takes a copy without the BackupConfigurationSchedule entry
        rbc = self.backup_config

        keys_to_remove = []

        if self.dict_source == 'agent-configuration':
            keys_to_remove = ['BackupConfigurationId',
                              'BackupConfigurationScheduled']

        elif self.dict_source == 'backup-configuration':
            keys_to_remove = ['LastRunBackupReportId',
                              'LastRunTime']

        else:
            raise ValueError('Unknown backup configuration source. Unable to clean the dictionary')

        for key in keys_to_remove:
            del rbc[key]

        return rbc

    @property
    def Configuration(self):
        """
        Dictionary object containing the backup configuration
        """
        return self.backup_config

    @property
    def ConfigurationId(self):
        """
        Id of the Backup Configuration

        Returns:
            The ID if it is set; otherwise None
        """
        return self.backup_config['BackupConfigurationId']

    @ConfigurationId.setter
    def ConfigurationId(self, backup_id):
        """
        Set the Backup Configuration Id
        """
        if isinstance(backup_id, types.IntType) or isinstance(backup_id, types.NoneType):
            self.backup_config['BackupConfigurationId'] = backup_id
        else:
            raise TypeError('backup_id is not an Integer Type or None Type')

    @property
    def ConfigurationName(self):
        """
        Name of the Backup Configuration as seen in RAX ControlPanel
        """
        return self.backup_config['BackupConfigurationName']

    @ConfigurationName.setter
    def ConfigurationName(self, name):
        """
        Retrieve the Configuration Name
        """
        if isinstance(name, types.StringTypes):
            self.backup_config['BackupConfigurationName'] = name
        else:
            raise TypeError('name is not a String Type')

    @property
    def MachineAgentId(self):
        """
        Machine Agent ID for the system where the Backup Configuration is to be run
        """
        return self.backup_config['MachineAgentId']

    @MachineAgentId.setter
    def MachineAgentId(self, machine_agent_id):
        """
        Retrieve the Machine Agent ID
        """
        if isinstance(machine_agent_id, types.IntType):
            self.backup_config['MachineAgentId'] = machine_agent_id
        else:
            raise TypeError('machine agent is not an IntType - {0:}'.format(type(machine_agent_id)))

    @property
    def Active(self):
        """
        Is the backup configuration active/in-use? (True/False)
        """
        return self.backup_config['IsActive']

    @Active.setter
    def Active(self, is_active):
        """
        Retrieve the backup configuration status
        """
        if isinstance(is_active, types.BooleanType):
            self.backup_config['IsActive'] = is_active
        else:
            raise TypeError('is_active is not a BooleanType')

    @property
    def VersionRetention(self):
        """
        Retention period for the data backed up with this backup configuration
            0 for indefinite
            30 for 30 days
            60 for 60 days
        """
        return self.backup_config['VersionRetention']

    @VersionRetention.setter
    def VersionRetention(self, retention):
        """
        Retrieve the retention period
        """
        if isinstance(retention, types.IntType):
            valid_values = (0, 30, 60)
            if retention in valid_values:
                self.backup_config['VersionRetention'] = retention
            else:
                raise ValueError('retention is not in {0:}'.format(valid_values))
        else:
            raise TypeError('retention is not an IntType')

    @property
    def Scheduled(self):
        """
        Backup Schedule
        """
        return self.backup_config['BackupConfigurationScheduled']

    @Scheduled.setter
    def Scheduled(self, schedule):
        """
        Retrieve the backup schedule
        """
        self.backup_config['BackupConfigurationScheduled'] = schedule

    @property
    def MissedBackupActionId(self):
        """
        Action to perform on a missed backup.
            1 = send notifications as soon as possible
            2 = send notifications at next scheduled time
        """
        return self.backup_config['MissedBackupActionId']

    @MissedBackupActionId.setter
    def MissedBackupActionId(self, action):
        """
        Retrieve the missed backup action id
        """
        if isinstance(action, types.IntType):
            valid_values = (1, 2)
            if action in valid_values:
                self.backup_config['MissedBackupActionId'] = action
            else:
                raise ValueError('action is not in {0:}'.format(valid_values))
        else:
            raise TypeError('action is not an IntType')

    @property
    def Frequency(self):
        """
        Frequency for how often to run the backup (Manually, Hourly, Daily, or Weekly)
        """
        return self.backup_config['Frequency']

    @Frequency.setter
    def Frequency(self, frequency):
        """
        Retrieve the backup frequency
        """
        if isinstance(frequency, types.StringTypes):
            valid_values = ('Manually', 'Hourly', 'Daily', 'Weekly')
            if frequency in valid_values:
                self.backup_config['Frequency'] = frequency
            else:
                raise ValueError('frequency is not in {0:}'.format(valid_values))
        else:
            raise TypeError('frequency is not a StringType')

    @property
    def StartTimeHour(self):
        """
        Hour when the backup is to be run
            1-12 when Frequency is Daily, or Weekly
            None when Frequencey is Manually or Hourly
        """
        return self.backup_config['StartTimeHour']

    @StartTimeHour.setter
    def StartTimeHour(self, hour):
        """
        Retrieve the hour the backup is to be run
        """
        if isinstance(hour, types.IntType) or isinstance(hour, types.NoneType):
            if (hour >= 1 and hour <= 12) or hour is None:
                self.backup_config['StartTimeHour'] = hour
            else:
                raise ValueError('hour is not between 1 and 12 inclusive, or is None')
        else:
            raise TypeError('hour is not an IntType or NoneType')

    @property
    def StartTimeMinute(self):
        """
        Minute when the backup is to be run
            0-59 when Frequency is Daily, or Weekly
            None when Frequency is Manually or Hourly
        """
        return self.backup_config['StartTimeMinute']

    @StartTimeMinute.setter
    def StartTimeMinute(self, minute):
        """
        Retrieve the minute of the hour the backup is to be run
        """
        if isinstance(minute, types.IntType) or isinstance(minute, types.NoneType):
            if (minute >= 0 and minute <= 59) or minute is None:
                self.backup_config['StartTimeMinute'] = minute
            else:
                raise ValueError('minute is not between 0 and 59 inclusive, or is None')
        else:
            raise TypeError('minute is not an IntType or NoneType')

    @property
    def StartTimeAmPm(self):
        """
        Division of day to run the backup
            AM for between midnight and noon
            PM for between noon and midnight
            None if Frequency is Manually or Hourly
        """
        return self.backup_config['StartTimeAmPm']

    @StartTimeAmPm.setter
    def StartTimeAmPm(self, AmPm):
        """
        Retrieve division of day the backup is to be run
        """
        if isinstance(AmPm, types.StringTypes) or isinstance(AmPm, types.NoneType):
            valid_values = ('AM', 'PM', None)
            if AmPm == "AM" or AmPm == "PM" or AmPm is None:
                self.backup_config['StartTimeAmPm'] = AmPm
            else:
                raise ValueError('AmPm ({1:}) is not in {0:}'.format(valid_values, AmPm))
        else:
            raise TypeError('AmPm is not StringTYpe or NoneType')

    @property
    def DayOfWeekId(self):
        """
        Day of week on which to run the backup
            0-6 for Sunday through Saturday
            None if Frequency is Manually, Hourly, or Daily
        """
        return self.backup_config['DayOfWeekId']

    @DayOfWeekId.setter
    def DayOfWeekId(self, dowid):
        """
        Retrieve the day of the week the backup is to be run
        """
        if isinstance(dowid, types.IntType) or isinstance(dowid, types.NoneType):
            if (dowid >= 0 and dowid <= 6) or dowid is None:
                self.backup_config['DayOfWeekId'] = dowid
            else:
                raise ValueError('dowid is not between 0 and 6 inclusive, or None')
        else:
            raise TypeError('dowid is not IntType or NoneType')

    @property
    def HourInterval(self):
        """
        Hour
            0-23 for Hourly
            None for Manually, Daily, or Weekly
        """
        return self.backup_config['HourInterval']

    @HourInterval.setter
    def HourInterval(self, hourinterval):
        """
        Retrieve the hour interval
        """
        if isinstance(hourinterval, types.IntType) or isinstance(hourinterval, types.NoneType):
            if (hourinterval >= 0 and hourinterval <= 23) or hourinterval is None:
                self.backup_config['HourInterval'] = hourinterval
            else:
                raise ValueError('HourInterval is not between 0 and 23 inclusive, or None')
        else:
            raise TypeError('HourInterval is not IntType or NoneType')

    @property
    def TimeZoneId(self):
        """
        Specifies the Time Zone in which the backup runs
        """
        return self.backup_config['TimeZoneId']

    @TimeZoneId.setter
    def TimeZoneId(self, timezone):
        """
        Retrieve the timezone in which the backup runs
        """
        if isinstance(timezone, types.StringTypes):
            self.backup_config['TimeZoneId'] = timezone
        else:
            raise TypeError('timezone is not a StringType')

    @property
    def NotifyRecipients(self):
        """
        E-mail address to send success/failure reports to
        """
        return self.backup_config['NotifyRecipients']

    @NotifyRecipients.setter
    def NotifyRecipients(self, recipients):
        """
        Retrieve the e-mail address for reports
        """
        if isinstance(recipients, types.StringTypes):
            self.backup_config['NotifyRecipients'] = recipients
        else:
            raise TypeError('recipients is not a StringType')

    @property
    def NotifySuccess(self):
        """
        E-mail reports on successful backup? (True/False)
        """
        return self.backup_config['NotifySuccess']

    @NotifySuccess.setter
    def NotifySuccess(self, notify):
        """
        Retrieve the status of reporting on successful backups
        """
        if isinstance(notify, types.BooleanType):
            self.backup_config['NotifySuccess'] = notify
        else:
            raise TypeError('notify is not a BooleanType')

    @property
    def NotifyFailure(self):
        """
        E-mail reports on failed backup? (True/False)
        """
        return self.backup_config['NotifyFailure']

    @NotifyFailure.setter
    def NotifyFailure(self, notify):
        """
        Retrieve the status of reporting on failed backups
        """
        if isinstance(notify, types.BooleanType):
            self.backup_config['NotifyFailure'] = notify
        else:
            raise TypeError('notify it not a BooleanType')

    def AddFolders(self, paths, excluded=False):
        """
        Add a series of absolute paths to the backup configuration
            paths is an array of absolute paths

            if excluded is True then the paths are excluded from the backup
            if excluded is False then the paths are included in the backup (default)
        """
        for path in paths:
            self.AddFolder(path, excluded)

    def IsFolderExcluded(self, absoluteFolderPath):
        """
        Return whether a given folder is already excluded
        """
        for entry in self.backup_config['Exclusions']:
            if entry['FileItemType'] == 'Folder' and entry['FilePath'] == absoluteFolderPath:
                return True

        return False

    def IsFolderIncluded(self, absoluteFolderPath):
        """
        Return whether a given folder is already excluded
        """
        for entry in self.backup_config['Inclusions']:
            if entry['FileItemType'] == 'Folder' and entry['FilePath'] == absoluteFolderPath:
                return True

        return False

    def AddFolder(self, absoluteFolderPath, excluded=False):
        """
        Add an absolute path to the backup configuration

            if excluded is True then the paths are excluded from the backup
            if excluded is False then the paths are included in the backup (default)
        """
        entry = {}
        entry['FilePath'] = absoluteFolderPath
        entry['FileItemType'] = 'Folder'
        if excluded:
            if not self.IsFolderExcluded(absoluteFolderPath):
                self.backup_config['Exclusions'].append(entry)
            else:
                self.log.debug('Folder {0:} is already in the exclusions'.format(absoluteFolderPath))
        else:
            if not self.IsFolderIncluded(absoluteFolderPath):
                self.backup_config['Inclusions'].append(entry)
            else:
                self.log.debug('Folder {0:} is already in the inclusions'.format(absoluteFolderPath))

    def AddFiles(self, files, excluded=False):
        """
        Add a series of files specified through their absolute path to the backup configuration

            if excluded is True then the paths are excluded from the backup
            if excluded is False then the paths are included in the backup (default)
        """
        for a_file in files:
            self.AddFile(a_file, excluded)

    def IsFileExcluded(self, absoluteFilePath):
        """
        Return whether a given file is already excluded
        """
        for entry in self.backup_config['Exclusions']:
            if entry['FileItemType'] == 'File' and entry['FilePath'] == absoluteFilePath:
                return True

        return False

    def IsFileIncluded(self, absoluteFilePath):
        """
        Return whether a given file is already excluded
        """
        for entry in self.backup_config['Inclusions']:
            if entry['FileItemType'] == 'File' and entry['FilePath'] == absoluteFilePath:
                return True

        return False

    def AddFile(self, absoluteFilePath, excluded=False):
        """
        Add a specific file specified through its absolute path to the backup configuration

            if excluded is True then the paths are excluded from the backup
            if excluded is False then the paths are included in the backup (default)
        """
        entry = {}
        entry['FilePath'] = absoluteFilePath
        entry['FileItemType'] = 'File'
        if excluded:
            if not self.IsFileExcluded(absoluteFilePath):
                self.backup_config['Exclusions'].append(entry)
            else:
                self.log.debug('File: {0:} is already in the inclusions'.format(absoluteFilePath))
        else:
            if not self.IsFileIncluded(absoluteFilePath):
                self.backup_config['Inclusions'].append(entry)
            else:
                self.log.debug('File: {0:} is already in the inclusions'.format(absoluteFilePath))


class Backups(Command):
    """
    Object to manage backup operations
    """

    def __init__(self, sslenabled, authenticator, apihost):
        """
        Initialize the backups
          sslenabled - True if using HTTPS; otherwise False
          authenticator - instance of cloudbackup.client.auth.Authentication to use
          apihost - server to use for API calls
        """
        super(self.__class__, self).__init__(sslenabled, apihost, '/')
        self.log = logging.getLogger(__name__)
        # save the ssl status for the various reinits done for each API call supported
        self.sslenabled = sslenabled
        self.authenticator = authenticator
        # Some cached data needed, set to invalid values by default
        self.agents = {}
        self.snapshot_id = None

    def CreateBackupConfiguration(self, backupinfo):
        """
        Create a backup configuration
          backupinfo is an instance of cloudbackup.client.backup.BackupConfiguration
        """
        if isinstance(backupinfo, BackupConfiguration):
            self.ReInit(self.sslenabled, "/v1.0/backup-configuration")
            self.headers['X-Auth-Token'] = self.authenticator.AuthToken
            self.headers['Content-Type'] = 'application/json'
            self.body = json.dumps(backupinfo.Configuration)
            res = requests.post(self.Uri, headers=self.Headers, data=self.Body)
            if res.status_code is 200:
                return True
            else:
                self.log.error('status code: %d', res.status_code)
                self.log.error('reason: ' + res.reason)
                self.log.error('error info: %s', res.text)
                return False
        else:
            raise TypeError('backup info is not an instance of BackupConfiguration')

    def RetrieveBackupConfiguration(self, backup_config_id):
        """
        Retrieve the specific backup configuration from the API
        """
        self.ReInit(self.sslenabled, '/v1.0/backup-configuration/{0:}'.format(backup_config_id))
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        res = requests.get(self.Uri, headers=self.Headers)
        if res.status_code is 200:
            return BackupConfiguration.from_dict(res.json(), source='backup-configuration')
        else:
            self.log.error('status code: %d', res.status_code)
            self.log.error('reason: ' + res.reason)
            self.log.error('error info: %s', res.text)
            raise ValueError('API returned error ({0:}): {1:} - {2:}'.format(res.status_code, res.reason, res.text))

    def UpdateBackupConfiguration(self, backupinfo):
        """
        Update the backup configuration
        """
        if isinstance(backupinfo, BackupConfiguration):
            self.log.error('Updating Backup Configuration {0:}'.format(backupinfo.ConfigurationId))
            self.ReInit(self.sslenabled, '/v1.0/backup-configuration/{0:}'.format(backupinfo.ConfigurationId))
            self.headers['X-Auth-Token'] = self.authenticator.AuthToken
            self.headers['Content-Type'] = 'application/json'
            self.body = json.dumps(backupinfo.to_update_dict)
            res = requests.put(self.Uri, headers=self.Headers, data=self.Body)
            if res.status_code is 200:
                return True
            else:
                self.log.error('status code: %d', res.status_code)
                self.log.error('reason: ' + res.reason)
                self.log.error('error info: %s', res.text)
                return False
        else:
            raise TypeError('backup info is not an instance of BackupConfiguration')

    def DeleteBackupConfiguration(self, backup_config_id):
        """
        Delete the backup configuration with the given backup configuration identifier
        """
        self.ReInit(self.sslenabled, "/v1.0/backup-configuration/" + str(backup_config_id))
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        res = requests.delete(self.Uri, headers=self.Headers)
        if res.status_code is 200:
            return True
        else:
            self.log.error('status code: %d', res.status_code)
            self.log.error('reason: ' + res.reason)
            self.log.error('error info: %s', res.text)
            return False

    def StartBackup(self, backup_config_id, retry=20):
        """
        Start a backup with the given backup configuration id
        """
        self.ReInit(self.sslenabled, "/v1.0/backup/action-requested")
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['Content-Type'] = 'application/json'
        o = {}
        o['Action'] = 'StartManual'
        o['Id'] = backup_config_id
        self.body = json.dumps(o)
        self.log.info('start manual backup request body: %s', json.dumps(o, sort_keys=False, indent=2))
        res = requests.post(self.Uri, headers=self.Headers, data=self.Body)
        self.log.info('start backup return code %s', res.status_code)
        self.log.info('start backup text reply %s', res.text)

        if res.status_code == 403:
            if retry <= 0:
                raise RuntimeError('Start Backup Failed - Access Forbidden: error code ({0:}) - {1:} - {2:}'.format(res.status_code, res.reason, res.text))
            else:
                self.log.warning('Received 403; retrying after 1 second')
                time.sleep(1)
                return self.StartBackup(backup_config_id, retry=(retry - 1))
        elif res.status_code != 200:
            self.log.error('status code: %d', res.status_code)
            self.log.error('reason: ' + res.reason)
            raise RuntimeError('Start Backup Failed - error code ({0:}) - {1:} - {2:}'.format(res.status_code, res.reason, res.text))

        self.snapshot_id = res.text
        self.log.info('snapshot ID: %s', self.snapshot_id)
        return self.snapshot_id

    def MonitorBackupProgress(self, snapshot_id, timeoutMilliseconds, pausePeriod=5.0):
        """
        Monitor the progress of the backup for the given snapshot id
        Timeout after timeoutMillseconds
        """
        self.ReInit(self.sslenabled, "/v1.0/backup/" + str(snapshot_id))
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        stoplist = ['Completed', 'Skipped', 'Missed', 'Stopped', 'Failed', 'CompletedWithErrors']
        start_time = int(round(time.time() * 1000))
        # poll for n-minutes
        finish_time = start_time + timeoutMilliseconds
        while ((int(round(time.time() * 1000))) < finish_time):
            # pause for so we don't hit the API/Agent too hard
            sleep(pausePeriod)
            res = requests.get(self.Uri, headers=self.Headers)
            if (res.status_code != 200):
                self.log.warn('status code: %d', res.status_code)
                self.log.error('reason: ' + res.reason)
                continue
            status_data = res.json()
            self.log.info('Backup ID: %s', status_data['BackupId'])
            self.log.info('  Current state: %s', status_data['CurrentState'])
            self.log.info('  Backup configuration ID: %s', status_data['BackupConfigurationId'])
            self.log.info('  Backup config name: %s', status_data['BackupConfigurationName'])
            self.log.info('  Machine agent ID: %s', status_data['MachineAgentId'])
            self.log.info('  Machine name: %s', status_data['MachineName'])
            self.log.info('  Datacenter: %s', status_data['Datacenter'])
            self.log.info('  Backup datacenter: %s', status_data['BackupDatacenter'])
            self.log.info('  State change time: %s', status_data['StateChangeTime'])
            self.log.info('  Encrypted: %s', status_data['IsEncrypted'])
            self.log.info('  Encryption key modulus: %s', status_data['EncryptionKey']['ModulusHex'])
            self.log.info('  Encryption key exponent: %s', status_data['EncryptionKey']['ExponentHex'])
            current_state = status_data['CurrentState']
            self.log.info('Current State: ' + current_state)
            if (current_state in stoplist):
                break

    def GetCompletedBackups(self, backup_config_id):
        '''
        Retrieves all the backups completed for a Backup Configuration
        '''
        self.ReInit(self.sslenabled, "/v1.0/backup/completed/" + str(backup_config_id))
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        res = requests.get(self.Uri, headers=self.Headers)
        if res.status_code is 200:
            snapshots = res.json()
        else:
            snapshots = list()
            self.log.error('status code: %d', res.status_code)
            self.log.error('reason: ' + res.reason)
            self.log.error('error info: %s', res.text)
        return snapshots

    def GetCompletedBackup(self, backup_config_id, snapshot_id):
        """
        Retrieve the information about a completed backup
          backup_config_id - backup configuration to retrieve snapshot data for
          snapshot_id - specific snapshot to get completion information for
        """
        snapshots = self.GetCompletedBackups(backup_config_id)
        if len(snapshots) > 0:
            try:
                for snapshot in snapshots:
                    if str(snapshot['BackupId']) == snapshot_id:
                        self.log.info('Backup ID: %s', str(snapshot['BackupId']))
                        self.log.info('  Configuration Id: %s', str(snapshot['BackupConfigurationId']))
                        self.log.info('  Configuration Name: %s', snapshot['BackupConfigurationName'])
                        self.log.info('  Machine Agent Id: %s', str(snapshot['MachineAgentId']))
                        self.log.info('  Machine Name: %s', snapshot['MachineName'])
                        self.log.info('  Completed Time: %s', snapshot['CompletedTime'])
                        self.log.info('  Bytes Searched: %s', snapshot['BytesSearched'])
                        self.log.info('  Number of Errors: %s', snapshot['NumErrors'])
                        return True
            except LookupError:
                self.log.error('Unable to retrieve backup completion information for backup configuration id ' + str(backup_config_id))
        return False

    def GetBackupReport(self, backup_id):
        """
        Retrieve the backup report the agent stored as a result of performing the backup
        Example:
            {
            u'CanRestore': True,
            u'ComputerName': u'ben-linux-dev',
            u'BytesSearched': u'60 KB',
            u'Diagnostics': u'No errors',
            u'BackupConfigurationId': 87643,
            u'Datacenter': u'DFW',
            u'BytesBackedUp': u'0 bytes',
            u'FilesBackedUp': u'0',
            u'FilesSearched': u'10',
            u'State': u'Completed',
            u'CompletedTime': u'/Date(1388424913000)/',
            u'BackupConfigurationIsDeleted': False,
            u'BackupConfigurationName': u'test_2013-12-05',
            u'Reason': u'Success',
            u'StartTime': u'/Date(1388424912000)/',
            u'MachineAgentId': 242370,
            u'Duration': u'00:00:01',
            u'BackupId': 8444451,
            u'ErrorList': [],
            u'NumErrors': 0,
            u'BackupDatacenter': u'DFW'
            }
        """
        self.ReInit(self.sslenabled, "/v1.0/backup/report/" + str(backup_id))
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['Content-Type'] = 'application/json'
        res = requests.get(self.Uri, headers=self.Headers)
        if res.status_code == 200:
            return res.json()
        else:
            msg = 'Unable to retrieve backup report for backup id ({0:}). Rackspace Cloud Backup API returned error status ({1:}) with text ({2:}) with reason ({3:})'.format(backup_id, res.status_code, res.text, res.reason)
            self.log.error(msg)
            raise RuntimeError(msg)

    def StartBackupRetry(self, parameters):
        """
        Performs the Start Backup via a loop to overcome a race condition in the agent.

        Parameters is a dictionary consisting of:
            'backupid' - the ID of the backup
            'backup_timeout' - Time to wait for the backup before failing via timeout
            'monitor_period' - time to sleep between monitor calls
            'retry_attempts' - number of times to retry

        Returns a dictionary that contains:
            'api_snapshotid' - Snapshot ID for a given backup in the API
            'agent_snapshotid' - Snapshot ID for a given backup in the Agent
            'backup_report' - the Backup Report
            'status' - True/False for success
        """
        output = {}
        # Assume failure
        output['status'] = False
        for retry in range(parameters['retry_attempts']):
            output['api_snapshotid'] = self.StartBackup(parameters['backupid'])
            self.log.info('Snapshot ID: {0:}'.format(output['api_snapshotid']))
            if output['api_snapshotid'] == -1:
                msg = 'Received an invalid snapshot id'
                self.log.error(msg)
                # Retry
                continue

            # Monitor the backup
            self.MonitorBackupProgress(output['api_snapshotid'], parameters['backup_timeout'], parameters['monitor_period'])

            # Retrieve the backup report
            output['backup_report'] = self.GetBackupReport(output['api_snapshotid'])
            self.log.info(output['backup_report'])
            output['agent_snapshotid'] = output['backup_report']['SnapshotId']
            if output['agent_snapshotid'] == -1:
                msg = 'Received an invalid snapshot id from the backup report. Reason: {0:} Diagnostics: {1:}'.format(output['backup_report']['Reason'], output['backup_report']['Diagnostics'])
                self.log.error(msg)
                # Retry
                continue

            # If we got here, then terminate the loop as we succeeded
            output['status'] = True
            break

        if not output['status']:
            raise RuntimeError('Failed to start the backup over {0:} attempts.'.format(parameters['retry_attempts']))

        return output

    def GetBackupsForRestore(self, machine_agent_id, backup_config_id):
        """
        Retrieve the restore configurations available

        Returns:
            A dictionary with two keys:
            code -- Status code for the request
            backups -- List of dictionaries of backup configuration available for restore
                Each Dictionary will have
                {
                   "BackupConfigurationId": 172418,
                   "BackupConfigurationName": "BackupConfig1",
                   "MachineName": "MBP0",
                   "MachineAgentId": 252036,
                   "IsEncrypted": false,
                   "PublicKeyHex": 10001,
                   "PublicKeyMod": "a5261939975948bb7a58dffe5ff54e65f0498f9175f5a0928
                   8810b8975871e99af3b5dd94057b0fc07535f5f97444504fa35169d461d0d30cf0
                   192e307727c065168c788771c561a9400fb49175e9e6aa4e23fe11af69e9412dd2
                   3b0cb6684c4c2429bce139e848ab26d0829073351f4acd36074eafd036a5eb8335
                   9d2a698d3",
                   "Flavor": "RaxCloudServer",
                   "LastSuccessfulBackupTime": "\/Date(1360701971000)\/"
                }
        """
        self.ReInit(self.sslenabled, "/v1.0/backup/availableforrestore")
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        res = requests.get(self.Uri, headers=self.Headers)
        availForRestore = dict()
        availForRestore['backups'] = list()
        availForRestore['code'] = res.status_code
        if res.status_code != 200:
            self.log.error('Received status code {0} when requesting available backups for restore for agent {1}'.format(res.status_code, machine_agent_id))
            self.log.error('reason: ' + res.reason)
            return availForRestore
        machine_config = res.json()
        for bkp in machine_config:
            if (backup_config_id == bkp['BackupConfigurationId']):
                availForRestore['backups'].append(bkp)
            else:
                continue
        if len(availForRestore['backups']) == 0:
            self.log.error('Unable to find any backups to restore for agent {0}'.format(machine_agent_id))
        return availForRestore


class RestoreConfiguration(object):
    '''
    Restore Configuration wrapper class
    '''
    @staticmethod
    def CreateRestoreConfigurationTemplate():
        '''Return a dictionary for creating restore configurations
        '''
        restoreconfig_template = dict()
        restoreconfig_template['BackupId'] = None
        restoreconfig_template['BackupMachineId'] = None
        restoreconfig_template['DestinationMachineId'] = None
        restoreconfig_template['DestinationPath'] = None
        restoreconfig_template['OverwriteFiles'] = False
        return restoreconfig_template

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.restore_config = RestoreConfiguration.CreateRestoreConfigurationTemplate()

    @property
    def BackupId(self):
        return self.restore_config['BackupId']

    @BackupId.setter
    def BackupId(self, value):
        self.restore_config['BackupId'] = value

    @property
    def BackupMachineId(self):
        return self.restore_config['BackupMachineId']

    @BackupMachineId.setter
    def BackupMachineId(self, value):
        self.restore_config['BackupMachineId'] = value

    @property
    def DestinationMachineId(self):
        return self.restore_config['DestinationMachineId']

    @DestinationMachineId.setter
    def DestinationMachineId(self, value):
        self.restore_config['DestinationMachineId'] = value

    @property
    def DestinationPath(self):
        return self.restore_config['DestinationPath']

    @DestinationPath.setter
    def DestinationPath(self, value):
        self.restore_config['DestinationPath'] = value

    @property
    def OverwriteFiles(self):
        return self.restore_config['OverwriteFiles']

    @OverwriteFiles.setter
    def OverwriteFiles(self, value):
        self.restore_config['OverwriteFiles'] = value

    # TODO: Test
    @property
    def RestoreId(self):
        if 'RestoreId' in self.restore_config:
            return self.restore_config['RestoreId']
        else:
            return None

    # TODO: Test
    @RestoreId.setter
    def RestoreId(self, value):
        self.restore_config['RestoreId'] = value

    # TODO: Test
    @property
    def BackupConfigurationId(self):
        if 'BackupConfigurationId' in self.restore_config:
            return self.restore_config['BackupConfigurationId']
        else:
            return None

    # TODO: Test
    @BackupConfigurationId.setter
    def BackupConfigurationId(self, value):
        self.restore_config['BackupConfigurationId'] = value

    # TODO: Test
    @property
    def RestoreStateId(self):
        if 'RestoreStateId' in self.restore_config:
            return self.restore_config['RestoreStateId']
        else:
            return None

    # TODO: Test
    @RestoreStateId.setter
    def RestoreStateId(self, value):
        self.restore_config['RestoreStateId'] = value

    @property
    def Configuration(self):
        return self.restore_config


class Restores(Command):
    '''
    Object to manage restore operations
    '''
    def __init__(self, sslenabled, authenticator, apihost):
        super(self.__class__, self).__init__(sslenabled, apihost, '/')
        self.log = logging.getLogger(__name__)
        # save the ssl status for the various reinits done for each API call supported
        self.sslenabled = sslenabled
        self.authenticator = authenticator

    def CreateRestoreConfiguration(self, restoreinfo):
        ''' Create a restore configuration
        '''
        if isinstance(restoreinfo, RestoreConfiguration):
            self.ReInit(self.sslenabled, '/v1.0/restore')
            self.headers['X-Auth-Token'] = self.authenticator.AuthToken
            self.headers['Content-Type'] = 'application/json'
            self.body = json.dumps(restoreinfo.Configuration)
            self.log.info(self.body)
            self.log.info(self.authenticator.AuthToken)
            self.log.info(self.uri)
            res = requests.put(self.Uri, headers=self.Headers, data=self.Body)
            if res.status_code is 200:
                return res.json()
            else:
                self.log.error('status code: %d', res.status_code)
                self.log.error('reason: ' + res.reason)
                self.log.error('error info: %s', res.text)
                return dict()
        else:
            raise TypeError('restoreinfo is not an instance of RestoreConfiguration')

    # TODO: Test
    def UpdateRestoreConfiguration(self, restoreinfo):
        if 'RestoreId' not in restoreinfo or 'BackupConfigurationId' not in restoreinfo or 'RestoreStateId' not in restoreinfo:
            self.log.error('Update Restore Configuration Request is missing elements')
            return (False, None)
        else:
            return self.CreateRestoreConfiguration(restoreinfo)

    # TODO: Test
    def DeleteRestoreConfiguration(self, restore_file_id):
        self.ReInit(self.sslenabled, '/v1.0/restore/files/{0}'.format(restore_file_id))
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        res = requests.delete(self.Uri, headers=self.Headers)
        if res.status_code is 200:
            return True
        else:
            self.log.error('status code: %d', res.status_code)
            self.log.error('reason: ' + res.reason)
            self.log.error('error info: %s', res.text)
            return False

    # TODO: Test
    def __IncExcReq(self, req):
        self.ReInit(self.sslenabled, "/v1.0/restore/files")
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['Content-Type'] = 'application/json'
        self.body = json.dumps(req)
        res = requests.put(self.Uri, headers=self.Headers, data=self.Body)
        if (res.status_code != 200):
            self.log.error('status code: %d', res.status_code)
            self.log.error('reason: ' + res.reason)
            return False
        return True

    # TODO: Test
    def __IncExcFiles(self, restore_config_id, filepath, filetype, rfilter, filepathencoded, fileid):
        o = dict()
        o['ParentId'] = restore_config_id
        o['FilePath'] = filepath
        o['FileItemType'] = filetype
        o['Filter'] = rfilter
        if filepathencoded is not None:
            o['FilePathEncoded'] = filepathencoded
        if fileid is not None:
            o['FileId'] = fileid
        return self.__IncExcReq(o)

    # TODO: Test
    def IncludeFile(self, restore_config_id, filepath, filepathencoded=None, fileid=None):
        return self.__IncExcFiles(restore_config_id, filepath, 0, 2, filepathencoded, fileid)

    # TODO: Test
    def IncludePath(self, restore_config_id, filepath, filepathencoded=None, fileid=None):
        return self.__IncExcFiles(restore_config_id, filepath, 1, 1, filepathencoded, fileid)

    # TODO: Test
    def IncludeDatabase(self, restore_config_id, filepath, filepathencoded=None, fileid=None):
        return self.__IncExcFiles(restore_config_id, filepath, 2, 1, filepathencoded, fileid)

    # TODO: Test
    def ExcludeFile(self, restore_config_id, filepath, filepathencoded=None, fileid=None):
        return self.__IncExcFiles(restore_config_id, filepath, 0, 2, filepathencoded, fileid)

    # TODO: Test
    def ExcludePath(self, restore_config_id, filepath, filepathencoded=None, fileid=None):
        return self.__IncExcFiles(restore_config_id, filepath, 1, 2, filepathencoded, fileid)

    # TODO: Test
    def ExcludeDatabase(self, restore_config_id, filepath, filepathencoded=None, fileid=None):
        return self.__IncExcFiles(restore_config_id, filepath, 2, 2, filepathencoded, fileid)

    # TODO: Test
    def ListIncExcFiles(self, restore_config_id):
        self.ReInit(self.sslenabled, '/v1.0/restore/files/{0}'.format(restore_config_id))
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        res = requests.get(self.Uri, headers=self.Headers)
        if res.status_code is 200:
            return res.json()
        else:
            self.log.error('status code: %d', res.status_code)
            self.log.error('reason: ' + res.reason)
            self.log.error('error info: %s', res.text)
            return dict()

    def __StartStopRestore(self, req, retry=20):
        self.ReInit(self.sslenabled, "/v1.0/restore/action-requested")
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['Content-Type'] = 'application/json'
        self.body = json.dumps(req)
        res = requests.post(self.Uri, headers=self.Headers, data=self.Body)
        if res.status_code == 403:
            if retry <= 0:
                self.log.error('Failed due to access forbidden')
                self.log.error('status code: %d', res.status_code)
                self.log.error('reason: ' + res.reason)
            else:
                self.log.warning('Received 403; retrying after 1 second')
                time.sleep(1)
                return self.__StartStopRestore(req, retry=(retry - 1))
        elif res.status_code != 204:
            self.log.error('status code: %d', res.status_code)
            self.log.error('reason: ' + res.reason)
            return False

        return True

    def StartRestore(self, restoreId, encrypted=None):
        ''' Start Restore operation

        Arguments:
        restoreId
        encrypted -- Encrypted key

        Returns a boolean
        '''
        o = dict()
        o['Action'] = 'StartManual'
        if encrypted is not None:
            o['EncryptedPassword'] = encrypted
        o['Id'] = restoreId
        return self.__StartStopRestore(o)

    def StartRestoreRetry(self, parameters):
        '''
        Start Restore operation

        parameters is a dictionary consisting of:
            'restoreId' - the ID of the restore
            'encrypted' - Encrypted key
            'restore_timeout' - TIme to wait for the restore before failing via timeout
            'monitor_period' - time to sleep between monitor calls
            'retry_attempts' - number of times to retry

        Returns a dictionary that contains:
            'restore_report' - the Restore Report
            'status' - True/False for success
        '''
        output = {}
        # Assume failure
        output['status'] = False
        for retry in range(parameters['retry_attempts']):
            # Try to start the restore
            if self.StartRestore(parameters['restoreId'], parameters['encrypted']):

                # Monitor the status of the restore
                self.MonitorRestoreProgress(parameters['restoreId'], parameters['restore_timeout'], parameters['monitor_period'])

                # Get the backup report
                output['restore_report'] = self.GetRestoreReport(parameters['restoreId'])

                if output['restore_report']['Reason'] != 'Success':
                    msg = 'Failed to start the restore operationg. Reason: {0:} Diagnostics: {1:}'.format(output['restore_report']['Reason'], output['restore_report']['Diagnostics'])
                    self.log.error(msg)
                    # Retry
                    continue

                # If we got here, then terminate the loop as we succeeded
                output['status'] = True
                break

        if not output['status']:
            raise RuntimeError('Failed to start the restore over {0:} attempts.'.format(parameters['retry_attempts']))

        return output

    # TODO: Test
    def StopRestore(self, restoreId):
        ''' Stop Restore operation

        Returns a boolean
        '''
        o = dict()
        o['Action'] = 'StopManual'
        o['Id'] = restoreId
        return self.__StartStopRestore(o)

    def GetRestoreDetails(self, restoreId):
        ''' Get details about a Restore

        Returns a dictionary with details about the restore operation. The keys
        would be:
            RestoreId
            BackupId
            BackupMachineId
            DestinationMachineId
            OverwriteFiles
            BackupConfigurationId
            BackupConfigurationName
            BackupRestorePoint
            MachineAgentId
            BackupMachineName
            BackupFlavor
            DestinationMachineName
            DestinationPath
            IsEncrypted
            EncryptedPassword
            PublicKey
            RestoreStateId
            Inclusions
            Exclusions
        '''
        self.ReInit(self.sslenabled, '/v1.0/restore/{0}'.format(restoreId))
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        res = requests.get(self.Uri, headers=self.Headers)
        if res.status_code is 200:
            return res.json()
        else:
            self.log.error('status code: %d', res.status_code)
            self.log.error('reason: ' + res.reason)
            self.log.error('error info: %s', res.text)
            return dict()

    def MonitorRestoreProgress(self, restoreId, timeoutMilliseconds, pausePeriod=5.0):
        ''' Monitor the progress of a restore operation

        Arguments:
        restoreId
        timeoutMilliseconds -- maximum amount of time (ms) the operation will last
        pausePediod
        '''
        status = dict()
        status[0] = 'Creating'
        status[1] = 'Queued'
        status[2] = 'InProgress'
        status[3] = 'Completed'
        status[4] = 'Stopped'
        status[5] = 'Failed'
        status[6] = 'StartRequested'
        status[7] = 'StopRequested'
        status[8] = 'Completed WithErrors'
        status[9] = 'Preparing'

        stoplist = (3, 4, 5, 7, 8)
        start_time = int(round(time.time() * 1000))
        # poll for n-minutes
        finish_time = start_time + timeoutMilliseconds
        while ((int(round(time.time() * 1000))) < finish_time):
            # pause for so we don't hit the API/Agent too hard
            sleep(pausePeriod)
            respbody = self.GetRestoreDetails(restoreId)
            if len(respbody.keys()) == 0:
                self.log.warn('Did not successful response')
                continue
            current_state = respbody['RestoreStateId']
            self.log.info('Current State: {0}'.format(status[current_state]))
            if (current_state in stoplist):
                break

    def GetRestoreReport(self, restoreId):
        ''' Returns a report about a specific Restore operation

        Returns a dictionary with the following keys:
            BackupConfigurationId
            BackupConfigurationName
            BackupReportId
            RestorePoint
            StartTime
            CompletedTime
            Duration
            OriginatingComputerName
            State
            NumFilesRestored
            NumBytesRestored
            RestoreDestination
            RestoreDestinationMachineId
            NumErrors
            Reason
            Diagnostics
            ErrorList
        '''
        self.ReInit(self.sslenabled, '/v1.0/restore/report/{0}'.format(restoreId))
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        res = requests.get(self.Uri, headers=self.Headers)
        if res.status_code is 200:
            return res.json()
        else:
            self.log.error('status code: %d', res.status_code)
            self.log.error('reason: ' + res.reason)
            self.log.error('error info: %s', res.text)
            return dict()
