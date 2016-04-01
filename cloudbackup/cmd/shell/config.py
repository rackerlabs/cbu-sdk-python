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
            }
        }
        """
        self._command_line = commandLineData

    def __hasCommandLineOverride(self, parameter):
        parameterLookups = {
            'userType': ('user', 'type'),
            'userId': ('user', 'id'),
            'authMethod': ('auth', 'method'),
            'authValue': ('auth', 'value')
        }

        keys = None
        if parameter in parameterLookups:
            keys = parameterLookups[parameter]
            self.logger.info(
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
            level = None
            while index < len(keys):
                if keys[index] in self._command_line:
                    level = keys[index]
                    index = index + 1
                else:
                    level = None
                    break

            if not type(level) is dict:
                return level

        return None

    def __valueOrOverride(self, valueName, valueType, value):
        overrideValue = self.__hasCommandLineOverride(valueType)
        if overrideValue is None:
            self.logger.info(
                'Config - {0} - No command-line value found. '
                'Accepting value "{1}"'
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
                'invalid user type {0}. Acceptable values are: {1}'.format(
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
                'invalid auth method {0}. Acceptable values are: {1}'.format(
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
            'authValue',
            authCredentials
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

        self.validate(
            'JSON file: {0}'
            .format(
                self._file_data['file'].name
            )
        )
