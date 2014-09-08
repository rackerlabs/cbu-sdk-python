"""
Rackspace Deuce API
"""
from __future__ import print_function

import logging
import requests

from cloudbackup.common.command import Command


class DeuceVault(Command):
    """
    Deuce Vault Functionality
    """

    def __init__(self, sslenabled, authenticator, apihost):
        """
        Initialize the Deuce Client access
            sslenabled - True if using HTTPS; otherwise false
            authenticator - instance of cloudbackup.clientl.auth.Authentication to use
            apihost - server to use for API calls
        """
        super(self.__class__, self).__init__(sslenabled, apihost, '/')
        self.log = logging.getLogger(__name__)
        # save the ssl status for the various reinits done for each API call supported
        self.sslenabled = sslenabled
        self.authenticator = authenticator


class DeuceClient(Command):
    """
    Object defining HTTP REST API calls for interacting with Deuce.
    """

    def __init__(self, sslenabled, authenticator, apihost, primary_dc):
        """
        Initialize the Deuce Client access
            sslenabled - True if using HTTPS; otherwise false
            authenticator - instance of cloudbackup.clientl.auth.Authentication to use
            apihost - server to use for API calls
        """
        super(self.__class__, self).__init__(sslenabled, apihost, '/')
        self.log = logging.getLogger(__name__)
        # save the ssl status for the various reinits done for each API call supported
        self.sslenabled = sslenabled
        self.authenticator = authenticator
        self.primary_dc = primary_dc

    def __update_headers(self):
        """
        Update common headers
        """
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['X-Project-ID'] = self.ProjectId
        for uri in self.authenticator.GetCloudFilesUri(self.primary_dc):
            if uri['name'] == 'snet':
                self.headers['X-Storage-URL'] = uri['uri']

    def __log_request_data(self):
        """
        Log the information about the request
        """
        self.log.debug('host: %s', self.apihost)
        self.log.debug('body: %s', self.Body)
        self.log.debug('headers: %s', self.Headers)
        self.log.debug('uri: %s', self.Uri)

    @property
    def ProjectId(self):
        """
        Return the project id to use
        """
        self.projectid = self.authenticator.AuthTenantId
        return self.projectid

    def CreateVault(self, vaultname):
        """
        Create a Vault
            vaultname - name of vault to be created
        """
        self.ReInit(self.sslenabled, '/v1.0/{0:}'.format(vaultname))
        self.__update_headers()
        self.__log_request_data()
        res = requests.put(self.Uri, headers=self.Headers)

        if res.status_code == 201:
            return True
        else:
            raise RuntimeError('Failed to create Vault. Error ({0:}): {1:}'.format(res.status_code, res.text))

    def DeleteVault(self, vaultname):
        """
        Delete a Vault
            vaultname - name of vault to be deleted
        """
        self.ReInit(self.sslenabled, '/v1.0/{0:}'.format(vaultname))
        self.__update_headers()
        self.__log_request_data()
        res = requests.delete(self.Uri, headers=self.Headers)

        if res.status_code == 204:
            return True
        else:
            raise RuntimeError('Failed to delete Vault. Error ({0:}): {1:}'.format(res.status_code, res.text))

    def VaultExists(self, vaultname):
        """
        Return the statistics on a Vault
            vaultname - name of vault to be deleted
        """
        self.ReInit(self.sslenabled, '/v1.0/{0:}'.format(vaultname))
        self.__update_headers()
        self.__log_request_data()
        res = requests.get(self.Uri, headers=self.Headers)

        if res.status_code == 204:
            return True
        elif res.status_code == 404:
            return False
        else:
            raise RuntimeError('Failed to determine if Vault exists. Error ({0:}): {1:}'.format(res.status_code, res.text))

    def GetVaultStatistics(self, vaultname):
        """
        Return the statistics on a Vault
            vaultname - name of vault to be deleted
        """
        self.ReInit(self.sslenabled, '/v1.0/{0:}'.format(vaultname))
        self.__update_headers()
        self.__log_request_data()
        res = requests.get(self.Uri, headers=self.Headers)

        if res.status_code == 200:
            return res.json()
        else:
            raise RuntimeError('Failed to get Vault statistics. Error ({0:}): {1:}'.format(res.status_code, res.text))

    def GetBlockList(self, vaultname, marker=None, limit=None):
        """
        Return the list of blocks in the vault
        """
        url = '/v1.0/{0:}/blocks'.format(vaultname)
        if marker is not None or limit is not None:
            # add the separator between the URL and the parameters
            url = url + '?'

            # Apply the marker
            if marker is not None:
                url = '{0:}marker={1:}'.format(url, marker)
                # Apply a comma if the next item is not none
                if limit is not None:
                    url = url + ','

            # Apply the limit
            if limit is not None:
                url = '{0:}limit={1:}'.format(url, limit)

        self.ReInit(self.sslenabled, url)
        self.__update_headers()
        self.__log_request_data()
        res = requests.get(self.Uri, headers=self.Headers)

        if res.status_code == 200:
            return res.json()
        else:
            raise RuntimeError('Failed to get Block list for Vault . Error ({0:}): {1:}'.format(res.status_code, res.text))
