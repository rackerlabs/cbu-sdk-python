from __future__ import print_function

import json
import logging

import cloudbackup.cmd.shell.exceptions


class CloudBackupConfig(object):

    USER_TYPE_VALUES = (
        'user',
        'tenantid',
        'tenantname'
    )

    AUTH_METHOD_VALUES = (
        'token',
        'apikey',
        'password'
    )

    AUTH_METHOD_COMBINATIONS = (
        ('token', ('tenantid')),
        ('apikey', USER_TYPE_VALUES),
        ('password', USER_TYPE_VALUES)
    )

    DATACENTERS = (
        'dfw',
        'hkg',
        'iad',
        'lon',
        'ord',
        'syd'
    )

    API_VERSIONS = (
        1.0,
        1,
        2
    )

    COMMANDLINE_DICT_MAPPING = {
        'userType': ('user', 'type'),
        'userId': ('user', 'id'),
        'authMethod': ('auth', 'method'),
        'authCredentials': ('auth', 'value'),
        'apiHost': ('options', 'apihost'),
        'apiVersion': ('options', 'apiversion'),
        'datacenter': ('options', 'datacenter'),
        'useServiceNet': ('options', 'useServiceNet')
    }

    def __init__(self, logger, commandLineData=None):
        self._command_line = None
        self._user_data = {
            'user': {
                'type': None,
                'id': None,
            },
            'auth': {
                'method': None,
                'credentials': None,
            },
            'options': {
                'apihost': None,
                'apiversion': 1,
                'datacenter': None,
                'servicenet': False,
            }
        }

        self.logger = logger
        self.commandLine = commandLineData

    def parse(self):
        raise NotImplemented

    def validate(self, authDataSource):
        values_to_check = (
            self.userType,
            self.userId,
            self.authMethod,
            self.authCredentials
        )
        if None in values_to_check:
            raise cloudbackup.cmd.shell.exceptions.CloudBackupApiBadAuthData(
                'Invalid Authentication Data. Check data source {0} - {1}'
                .format(
                    authDataSource,
                    values_to_check
                )
            )
        if not self.apiVersion in CloudBackupConfig.API_VERSIONS:
            raise cloudbackup.cmd.shell.exceptions.CloudBackupApiBadAuthData(
                'Invalid Authentication Data. Check data source {0} - {1}'
                .format(
                    authDataSource,
                    'apiVersion'
                )
            )
        
    @property
    def commandLine(self):
        return self._command_line

    @commandLine.setter
    def commandLine(self, commandLineData):
        """Set a dictionary containing command-line override values

        For the dictionary to provide the value values, it must be
        in the following format:

        {
            'user' : {
                'type': <string>,
                'id': <string>
            },
            'auth': {
                'method': <string>,
                'value': <string>
            },
            'options': (
                'apihost': <string> or None,
                'apiversion': integer,
                'datacenter': None,
                'useServiceNet': <boolean>
            }
        }
        """
        self._command_line = commandLineData
        self.logger.info(
            'User command-line data: {0}'
            .format(
                self._command_line
            )
        )

        self.logger.debug('Updating defaults based on command-line')
        for key in CloudBackupConfig.COMMANDLINE_DICT_MAPPING.keys():
            value = self.__hasCommandLineOverride(key)
            if not value is None:
                self.logger.debug(
                    'Found Command-line value: {0} = {1}'
                    .format(
                        key,
                        value
                    )
                )
                setattr(self, key, value)
        self.logger.debug('Finished applying command-line values')
                        

    def __hasCommandLineOverride(self, parameter):
        keys = None
        if parameter in CloudBackupConfig.COMMANDLINE_DICT_MAPPING:
            keys = CloudBackupConfig.COMMANDLINE_DICT_MAPPING[parameter]
            self.logger.debug(
                'Parameter {0} => Keys: {1}'
                .format(
                    parameter,
                    keys
                )
            )

        else:
            raise ValueError(
                'Programming error. Need to specify {0}'
                .format(
                    parameter
                )
            )

        if not self._command_line is None:
            index = 0
            level = self._command_line
            while index < len(keys):
                self.logger.debug(
                    'Index: {0} -> Key = {1}'
                    .format(
                        index,
                        keys[index],
                    )
                )
                if keys[index] in level:
                    self.logger.debug(
                        'Key[{0}] yielded new level'
                        .format(
                            keys[index]
                        )
                    )
                    level = level[keys[index]]
                    index = index + 1
                else:
                    level = None
                    break

            if not type(level) is dict:
                return level

        return None

    def __valueOrOverride(self, valueName, valueType, value):
        overrideValue = self.__hasCommandLineOverride(valueType)
        if overrideValue is None or overrideValue == value:
            if value is None:
                self.logger.info(
                    'Config - {0} - No command-line value found. '
                    'Accepting value "{1}"'
                    .format(
                        valueName,
                        value
                    )
                )
            else:
                self.logger.info(
                    'Config - {0} - Accepting value "{1}"'
                    .format(
                        valueName,
                        value
                    )
                )
            return value

        else:
            self.logger.info(
                'Config - {0} - Command-line value "{1}" takes precedences '
                'over "{2}"'
                .format(
                    valueName,
                    overrideValue,
                    value
                )
            )
                
            return overrideValue

    @property
    def userType(self):
        return self._user_data['user']['type']

    @userType.setter
    def userType(self, userType):
        if userType in CloudBackupConfig.USER_TYPE_VALUES:
            self.logger.info(
                'Config - User Type - Proposing: {0}'
                .format(
                    userType
                )
            )
            self._user_data['user']['type'] = self.__valueOrOverride(
                'User Type',
                'userType',
                userType
            )
        else:
            raise cloudbackup.cmd.shell.exceptions.CloudBackupApiBadAuthData(
                'invalid user type {0}. Acceptable values are: {1}'
                .format(
                    userType,
                    CloudBackupConfig.USER_TYPE_VALUES
                )
            )

    @property
    def userId(self):
        return self._user_data['user']['id']

    @userId.setter
    def userId(self, userId):
        self._user_data['user']['id'] = self.__valueOrOverride(
            'User Id',
            'userId',
            userId
        )

    @property
    def authMethod(self):
        return self._user_data['auth']['method']

    @authMethod.setter
    def authMethod(self, authMethod):
        if authMethod in CloudBackupConfig.AUTH_METHOD_VALUES:
            self._user_data['auth']['method'] = self.__valueOrOverride(
                'Auth Method',
                'authMethod',
                authMethod
            )
        else:
            raise cloudbackup.cmd.shell.exceptions.CloudBackupApiBadAuthData(
                'invalid auth method {0}. Acceptable values are: {1}'
                .format(
                    authMethod,
                    CloudBackupConfig.AUTH_METHOD_VALUES
                )
            )

    @property
    def authCredentials(self):
        return self._user_data['auth']['credentials']

    @authCredentials.setter
    def authCredentials(self, authCredentials):
        self._user_data['auth']['credentials'] = self.__valueOrOverride(
            'Auth Credentials',
            'authCredentials',
            authCredentials
        )

    @property
    def datacenter(self):
        return self._user_data['options']['datacenter']

    @datacenter.setter
    def datacenter(self, datacenter):
        if datacenter in CloudBackupConfig.DATACENTERS:
            self._user_data['options']['datacenter'] = self.__valueOrOverride(
                'Datacenter',
                'datacenter',
                datacenter
            )
        else:
            raise cloudbackup.cmd.shell.exceptions.CloudBackupApiBadParameters(
                'invalid data center - {0}. Acceptable values are: {1}'
                .format(
                    datacenter,
                    CloudBackupConfig.DATACENTERS
                )
            )

    @property
    def useServiceNet(self):
        return self._user_data['options']['servicenet']

    @useServiceNet.setter
    def useServiceNet(self, useServiceNet):
        if useServiceNet in (True, False):
            self._user_data['options']['servicenet'] = self.__valueOrOverride(
                'Use Service Net',
                'useServiceNet',
                useServiceNet
            )
        else:
            raise cloudbackup.cmd.shell.exceptions.CloudBackupApiBadParameters(
                'non-boolean value for useServiceNet - {0}. Acceptable values are: {1}'
                .format(
                    useServiceNet,
                    (True, False)
                )
            )

    @property
    def apiHost(self):
        return self._user_data['options']['apihost']

    @apiHost.setter
    def apiHost(self, apihost):
        self._user_data['options']['apihost'] = self.__valueOrOverride(
            'Cloud Backup API',
            'apiHost',
            apihost
        )

    @property
    def apiVersion(self):
        # b/c 1.0 must be 1.0 not simply 1
        if self._user_data['options']['apiversion'] == 1:
            return 1.0
        else:
            return self._user_data['options']['apiversion']

    @apiVersion.setter
    def apiVersion(self, apiVersion):
        if apiVersion in CloudBackupConfig.API_VERSIONS:
            self._user_data['options']['apiversion'] = self.__valueOrOverride(
                'Cloud Backup API Version',
                'apiVersion',
                apiVersion
            )
        else:
            raise cloudbackup.cmd.shell.exceptions.CloudBackupApiBadParameters(
                'invalid apiVersion - {0}. Acceptable values are: {1}'
                .format(
                    apiVersion,
                    CloudBackupConfig.API_VERSIONS
                )
            )


class CloudBackupFileConfig(CloudBackupConfig):

    def __init__(self, auth_fileobj, *args, **kwargs):
        super(CloudBackupFileConfig, self).__init__(*args, **kwargs)
        self._file_data = {
            'file': auth_fileobj,
            'json': None
        }

        self.parse()

    @property
    def json(self):
        return self._file_data['json']

    def parse(self):
        self._file_data['json'] = json.load(
            self._file_data['file']
        )

        self.logger.debug(
            'JSON Config File - Available Options: {0}'
            .format(
                self.json.keys()
            )
        )

        if 'user_type' in self.json:
            self.userType = self.json['user_type']
        else:
            self.userType = 'user'

        if 'user' in self.json:
            self.userId = self.json['user']


        for METHOD, VALUES in CloudBackupConfig.AUTH_METHOD_COMBINATIONS:
            
            if METHOD in self.json:
                self.logger.info(
                    'Found Auth Method {0}'
                    .format(
                        METHOD
                    )
                )
                if self.userType in VALUES:
                    self.logger.info(
                        'Accepting Auth Method {0}'
                        .format(
                            METHOD
                        )
                    )
                    self.authMethod = METHOD
                    self.authCredentials = self.json[METHOD]
                    break

                else:
                    self.logger.info(
                        'User Type {0} not acceptable for Auth Method {1}'
                        .format(
                            self.userType,
                            METHOD
                        )
                    )

        if 'datacenter' in self.json:
            self.datacenter = self.json['datacenter']

        if 'useServiceNet' in self.json:
            self.useServiceNet = self.json['useServiceNet']

        if 'apihost' in self.json:
            self.apiHost = self.json['apihost']

        if 'apiversion' in self.json:
            self.apiVersio = self.json['apiversion']

        self.validate(
            'JSON file: {0}'
            .format(
                self._file_data['file'].name
            )
        )
