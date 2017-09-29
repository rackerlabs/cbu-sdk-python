"""
Rackspace Cloud Files
"""
import gzip
import hashlib
import logging
import os.path
import requests
import time

from cloudbackup.common.command import Command

requests.packages.urllib3.disable_warnings()



class CloudFiles(Command):
    """
    Primary Cloud Files API Class
    """

    def __init__(self, sslenabled, authenticator, publicnet=False):
        """
        Setup the CloudFiles API Class in the same manner as cloudbackup.common.Command
        """
        super(self.__class__, self).__init__(sslenabled, 'localhost', '/')
        # save the ssl status for the various reinits done for each API call supported
        self.sslenabled = sslenabled
        self.authenticator = authenticator
        self.auth = authenticator
        self.usepublicnet = publicnet
        self.log = logging.getLogger(__name__)

    def _get_container(self, container):
        """
        Return the publicnet or servicenet container name.

        Note: servicenet container names start with 'snet-'.
        """
        if self.usepublicnet:
            if container.startswith('snet-'):
                return container[5:]
        return container

    def GetContainers(self, uri, limit=-1, marker=''):
        """
        List all containers for the current account
        """
        self.apihost = self._get_container(uri)
        urioptions = '?format=json'
        if not limit is -1:
            urioptions += '&limit=%d' % limit
        if len(marker):
            urioptions += '&marker=%s' % marker
        self.ReInit(self.sslenabled, urioptions)
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        self.log.debug('uri: %s', self.Uri)
        self.log.debug('headers: %s', self.Headers)
        try:
            res = requests.get(self.Uri, headers=self.Headers)
        except requests.exceptions.SSLError as ex:
            self.log.error('Requests SSLError: {0}'.format(str(ex)))
            res = requests.get(self.Uri, headers=self.Headers, verify=False)
        if res.status_code == 200:
            # We have a list in JSON format
            return res.json()
        elif res.status_code == 204:
            # Nothing left to retrieve
            return {}
        else:
            # Error
            self.log.error('Error retrieving list of containers: (code=' + str(res.status_code) + ', text=\"' + res.text + '\")')
            return {}

    def GetContainerObjects(self, uri, container, limit=-1, marker=''):
        """
        List the objects in a container under the current account
        """
        self.apihost = self._get_container(uri)
        urioptions = '/' + container + '?format=json'
        if not limit is -1:
            urioptions += '&limit=%d' % limit
        if len(marker):
            urioptions += '&marker=%s' % marker
        self.ReInit(self.sslenabled, urioptions)
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        self.log.debug('uri: %s', self.Uri)
        self.log.debug('headers: %s', self.Headers)
        try:
            res = requests.get(self.Uri, headers=self.Headers)
        except requests.exceptions.SSLError as ex:
            self.log.error('Requests SSLError: {0}'.format(str(ex)))
            res = requests.get(self.Uri, headers=self.Headers, verify=False)
        if res.status_code == 200:
            # We have a list in JSON format
            return res.json()
        elif res.status_code == 204:
            # Nothing left to retrieve
            return {}
        else:
            # Error
            self.log.error('Error retrieving list of containers: (code=' + str(res.status_code) + ', text=\"' + res.text + '\")')
            return {}

    def _verify_snapshot(self, container, uripath, snapshot):
        """
        Look at the Cloud Backup Container in CloudFiles for the agent to find its latest VaultDB
            container - the container in CloudFiles in which to look for the active VaultDB
            uripath - the path in the CloudFiles container under which to look for the DB directory contents
            snapshot - the snapshot desired

        Returns a python dictionary with the following data:
            - 'name' - the name within the container of the VaultDB file
            - 'dbsnapshotid' - the snapshot id of the returned database
            - 'hash' - the MD5 hash of the VaultDB
            - 'cf-hash' - the MD5 hash of the VaultDB as it came from Cloud Files
            - 'last_modified' - a Date-Time Stamp of the last modification to the VaultDB
            - 'bytes' - the size in bytes of the VaultDB file
            - 'content_type' - the content type of th VaultDB file
        """
        self.apihost = self._get_container(container)
        # We take the container and only request the data come back in JSON format
        # The uripath is used later
        self.ReInit(self.sslenabled, '?format=json')
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        self.log.debug('uri: %s', self.Uri)
        self.log.debug('headers: %s', self.Headers)
        try:
            res = requests.get(self.Uri, headers=self.Headers)
        except requests.exceptions.SSLError as ex:
            self.log.error('Requests SSLError: {0}'.format(str(ex)))
            res = requests.get(self.Uri, headers=self.Headers, verify=False)
        if res.status_code == 200:
            self.log.debug('Received data from CloudFiles...looking for VaultDB with Snapshot ID ' + str(snapshot))
            cf_data = res.json()
            try:
                # Find the master database by finding the largest ordinal in the listing
                # Unfortunately there's
                db_master = {}
                db_master['name'] = 'INVALID'
                db_ordinal = -1
                # Note: By appending the '/' we elimiate /DB from being put into the list, and
                #       Also eliminate a LookupError from occurring as it won't have an ordinal
                #       in its name for the cf_entry_ordinal parsing line
                dbpath = uripath + '/DB/'

                for cf_entry in cf_data:
                    if cf_entry['name'].startswith(dbpath):
                        self.log.debug('Checking DB path: ' + cf_entry['name'])
                        cf_entry_ordinal = int(cf_entry['name'].rpartition('/')[2])
                        self.log.debug('Checking: DB ordinal (' + str(cf_entry_ordinal) + ') == Snapshot (' + str(snapshot) + ')? ' + str(cf_entry_ordinal == snapshot))
                        if cf_entry_ordinal == snapshot:
                            self.log.debug('Found database')
                            self.log.debug('Changing ordinal from ' + str(db_ordinal) + ' to ' + str(cf_entry_ordinal))
                            self.log.debug('Changing db master from ' + db_master['name'] + ' to ' + cf_entry['name'])
                            db_ordinal = cf_entry_ordinal
                            db_master = cf_entry
                            # Note: The ordinal also happens to be the internal snapshot id for that database
                            db_master['dbsnapshotid'] = snapshot
                            db_master['cf-hash'] = db_master['hash']
                            db_master['hash'] = db_master['cf-hash'].upper()
                            return db_master

                # We did not find the specified database
                self.log.error('Database with snapshot id ' + str(snapshot) + ' in the name could not be located.')
                raise RuntimeError
            except LookupError:
                self.log.error('Unable to lookup CloudFile Container Item Name in specified container.')
                raise
        elif res.status_code == 204:
            self.log.debug('No data in the specified container')
            raise RuntimeError('No data in the specified container')
        else:
            self.log.error('Error retrieving data (' + str(res.status_code) + ') - ' + res.text)
            raise RuntimeError('Error retrieving data (' + str(res.status_code) + ') - ' + res.text)

    def _auto_detect_snapshot(self, container, uripath):
        """
        Look at the Cloud Backup Container in CloudFiles for the agent to find its latest VaultDB
            container - the container in CloudFiles in which to look for the active VaultDB
            uripath - the path in the CloudFiles container under which to look for the DB directory contents

        Returns a python dictionary with the following data:
            - 'hash' - the MD5 hash of the VaultDB
            - 'last_modified' - a Date-Time Stamp of the last modification to the VaultDB
            - 'bytes' - the size in bytes of the VaultDB file
            - 'name' - the name within the container of the VaultDB file
            - 'content_type' - the content type of th VaultDB file
            - 'dbsnapshotid' - the snapshot id of the returned database
        """
        self.apihost = self._get_container(container)
        # We take the container and only request the data come back in JSON format
        # The uripath is used later
        dbpath = uripath + '/DB/'
        self.ReInit(self.sslenabled, '?format=json&path={0:}'.format(dbpath))
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        self.log.debug('uri: %s', self.Uri)
        self.log.debug('headers: %s', self.Headers)
        try:
            res = requests.get(self.Uri, headers=self.Headers)
        except requests.exceptions.SSLError as ex:
            self.log.error('Requests SSLError: {0}'.format(str(ex)))
            res = requests.get(self.Uri, headers=self.Headers, verify=False)
        if res.status_code == 200:
            cf_data = res.json()
            try:
                # Find the master database by finding the largest ordinal in the listing
                # Unfortunately there's
                db_master = {}
                db_master['name'] = 'INVALID'
                db_ordinal = -1
                # Note: By appending the '/' we elimiate /DB from being put into the list, and
                #       Also eliminate a LookupError from occurring as it won't have an ordinal
                #       in its name for the cf_entry_ordinal parsing line

                self.log.debug('Looking for object path {0:}'.format(dbpath))

                for cf_entry in cf_data:
                    self.log.debug('Checking path {0:}'.format(cf_entry['name']))
                    if cf_entry['name'].startswith(dbpath):
                        cf_entry_ordinal = int(cf_entry['name'].rpartition('/')[2])
                        if cf_entry_ordinal > db_ordinal:
                            self.log.debug('Changing ordinal from ' + str(db_ordinal) + ' to ' + str(cf_entry_ordinal))
                            self.log.debug('Changing db master from ' + db_master['name'] + ' to ' + cf_entry['name'])
                            db_ordinal = cf_entry_ordinal
                            db_master = cf_entry
                            # Note: The ordinal also happens to be the internal snapshot id for that database
                            db_master['dbsnapshotid'] = db_ordinal
                if not db_master['name'] == 'INVALID':
                    db_master['cf-hash'] = db_master['hash']
                    db_master['hash'] = db_master['cf-hash'].upper()
                    return db_master
                else:
                    self.log.error('Unable to locate a VaultDB in the specified container')
                    raise UserWarning('Unable to locate VaultDB in container ' + container + ' matching ' + uripath)
            except LookupError:
                self.log.error('Unable to lookup CloudFile Container Item Name in specified container.')
                return {}
        elif res.status_code == 204:
            self.log.debug('No data in the specified container')
            raise RuntimeError
        else:
            self.log.error('Error retrieving data (' + str(res.status_code) + ') - ' + res.text)
            raise RuntimeError

    def GetSnapshotPath(self, vaultdb_data, snapshotid):
        """
        Look at the VaultDB data and return a version updated for the given snapshotid

        Note: vaultdb_data is built by GetActiveDB() or WaitForActiveDb()

        Requires the following entries in the vaultdb_data:
            - 'name' - the name within the container of the VaultDB file

        Returns a dictionary with the following parameters:
            - 'name' - the name within the container of the VaultDB file
            - 'dbsnapshotid' - the snapshot id of the returned database
        """

        # Access the path of the incoming vaultdb
        dbpath = vaultdb_data['name']

        # Update the path for the specified snapshotid
        parts = list(dbpath.split('/'))
        parts[-1] = '{0:010}'.format(snapshotid)
        dbpath = '/'.join(parts)

        # Create the returned dictionary
        dbdata = {}
        dbdata['name'] = dbpath
        dbdata['dbsnapshotid'] = snapshotid

        return dbdata

    def GetActiveDB(self, container, uripath, snapshot=None):
        """
        Look at the Cloud Backup Container in CloudFiles for the agent to find its latest VaultDB
            container - the container in CloudFiles in which to look for the active VaultDB
            uripath - the path in the CloudFiles container under which to look for the DB directory contents
            snapshot - the snapshot id (agent version) for the database to download (optional)

        Note: If 'snapshot' is specified, then this function will try to get the database for that specific
            snapshot; however, if the call fails, then it will try to auto-find the database. The snapshot
            can be verified using the 'dbsnapshotid' entry in the returned dictionary.

        Returns a python dictionary with the following data:
            - 'hash' - the MD5 hash of the VaultDB
            - 'last_modified' - a Date-Time Stamp of the last modification to the VaultDB
            - 'bytes' - the size in bytes of the VaultDB file
            - 'name' - the name within the container of the VaultDB file
            - 'content_type' - the content type of th VaultDB file
            - 'dbsnapshotid' - the snapshot id of the returned database
        """
        if not (snapshot is None):
            try:
                return self._verify_snapshot(container, uripath, snapshot)
            except:
                return self._auto_detect_snapshot(container, uripath)
        else:
            return self._auto_detect_snapshot(container, uripath)

    def WaitForActiveDb(self, container, uripath, snapshot, timeoutMilliseconds):
        """
        Look at the Cloud Backup Container in CloudFiles for the agent to find its latest VaultDB
            container - the container in CloudFiles in which to look for the active VaultDB
            uripath - the path in the CloudFiles container under which to look for the DB directory contents
            snapshot - the snapshot id (agent version) for the database to download (optional)
            timeoutMilliseconds - the time in milliseconds to wait for the given database to show up in Cloud Files

        Returns a python dictionary with the following data:
            - 'hash' - the MD5 hash of the VaultDB
            - 'last_modified' - a Date-Time Stamp of the last modification to the VaultDB
            - 'bytes' - the size in bytes of the VaultDB file
            - 'name' - the name within the container of the VaultDB file
            - 'content_type' - the content type of th VaultDB file
            - 'dbsnapshotid' - the snapshot id of the returned database
        """
        if snapshot == -1:
            raise RuntimeError('Invalid snapshot id')

        start_time = int(round(time.time() * 1000))
        finish_time = start_time + timeoutMilliseconds

        result = None
        while ((int(round(time.time() * 1000))) < finish_time):
            try:
                self.log.debug('Attempting lookup of VaultDB with Snapshot {0:} - time {1:} '.format(snapshot, (int(round(time.time() * 1000)))))
                result = self._verify_snapshot(container, uripath, snapshot)
                if result['dbsnapshotid'] == snapshot:
                    break
                else:
                    result = None
                    time.sleep(1)
            except Exception as e:
                self.log.debug('Received Error: ' + str(e))
                # Slow it down so we don't spam/ddos Cloud Files
                time.sleep(1)
                result = None

        if result is None:
            msg = 'Unable to find database with snapshot id {0:} within {1:} ms.'.format(snapshot, timeoutMilliseconds)
            self.log.error(msg)
            raise RuntimeError(msg)
        else:
            return result

    def __GetLargeFileHashes(self, localpath):
        large_file_hashes = list()
        # 512 MB
        byte_boundary = 512 * 1024 * 1024
        # point_boundary = 1024 * 1024 * 1024
        byte_read_count = 1024

        lf_hash = hashlib.md5()
        count = 0
        with open(localpath, 'rb') as db_file:
            continue_loop = True
            while continue_loop:
                try:
                    chunk = db_file.read(byte_read_count)

                    if len(chunk) == 0:
                        raise EOFError

                    count = count + len(chunk)
                    lf_hash.update(chunk)
                    if count >= byte_boundary:
                        large_file_hashes.append(lf_hash.hexdigest())
                        lf_hash = hashlib.md5()
                        count = 0

                except EOFError:
                    continue_loop = False

        full_hash = hashlib.md5()
        h_count = 0
        for entry in large_file_hashes:
            h_count = h_count + 1
            full_hash.update(entry)

        hashes = {}
        hashes['hashes'] = large_file_hashes
        hashes['md5'] = full_hash.hexdigest().upper()

        return hashes

    def DownloadVaultDb(self, container, vaultdb_data, localpath, decompress=True, maximum_file_size_supported=(5 * 1024 * 1024 * 1024)):
        """
        Download the VaultDB from CloudFiles into a local path
            container - the CloudFiles container in which to find the Vault DB
            vaultdb_data - the CloudFiles data regarding the VaultDB (see GetActiveDB() for details)
            localpath - the local path at which to store the downloaded VaultDB
            decompress - whether or not to automatically decompress the downloaded vaultdb

        Note: There is a bug in the gzip library that causes a problem for decompressing large objects.

        Requires the following entries in the 'vaultdb_data' parameter:
            - 'name' - the name within the container of the VaultDB file

        Adds the following entries to the 'vaultdb_data' parameter:
            - 'md5' - the MD5 of the data on disk
            - 'compressed-md5' - the MD5 of the compressed data received from Cloud Files
            - 'sha1' - the SHA-1 of the data on disk
            - 'compressed-sha1' - the SHA-1 of the compressed data received from Cloud Files

            Note: The 'md5' and 'sha1' entries are only added if the vaultdb is
                automatically decompressed, e.g decompress = True
        """
        self.apihost = self._get_container(container)
        file_chunk_size = 4 * 1024 * 1024
        try:
            self.ReInit(self.sslenabled, '/' + vaultdb_data['name'])
            self.headers['X-Auth-Token'] = self.authenticator.AuthToken
            self.log.debug('uri: %s', self.Uri)
            self.log.debug('headers: %s', self.Headers)
            try:
                res = requests.get(self.Uri, headers=self.Headers, stream=True)
            except requests.exceptions.SSLError as ex:
                self.log.error('Requests SSLError: {0}'.format(str(ex)))
                res = requests.get(self.Uri, headers=self.Headers, verify=False, stream=True)
            if res.status_code == 404:
                raise UserWarning('Server failed to find the specified database')
            elif res.status_code >= 300:
                raise UserWarning('Server responded unexpectedly during download (Code: ' + str(res.status_code) + ' )')
            else:
                if maximum_file_size_supported is not None:
                    if int(res.headers['Content-Length']) >= maximum_file_size_supported:
                        raise NotImplementedError('The VaultDB is larger than the presently supported file size.')

                meter = {}
                meter['bytes-total'] = int(res.headers['Content-Length'])
                meter['bytes-remaining'] = int(res.headers['Content-Length'])
                meter['bar-count'] = 50
                meter['bytes-per-bar'] = meter['bytes-remaining'] // meter['bar-count']
                meter['block-size'] = min(file_chunk_size, meter['bytes-per-bar'])
                meter['chunks-per-bar'] = meter['bytes-per-bar'] // meter['block-size']
                meter['chunks'] = 0
                meter['bars-remaining'] = meter['bar-count']
                meter['bars-completed'] = 0
                self.log.info('Downloading database(gz): {0} bytes...'.format(meter['bytes-remaining']))
                self.log.info('[' + ' ' * meter['bar-count'] + ']')
                gzip_file = localpath + '.gz'
                compressed_md5_hash = hashlib.md5()
                compressed_sha1_hash = hashlib.sha1()
                with open(gzip_file, 'wb') as gzipped_db:
                    for db_chunk in res.iter_content(chunk_size=meter['block-size']):
                        gzipped_db.write(db_chunk)
                        compressed_md5_hash.update(db_chunk)
                        compressed_sha1_hash.update(db_chunk)
                        gzipped_db.flush()
                        os.fsync(gzipped_db.fileno())
                        meter['chunks'] += 1
                        if meter['chunks'] == meter['chunks-per-bar']:
                            meter['chunks'] = 0
                            meter['bars-completed'] += 1
                            meter['bars-remaining'] -= 1
                            self.log.info('[' + '-' * meter['bars-completed'] + ' ' * meter['bars-remaining'] + ']')
                vaultdb_data['compressed-md5'] = compressed_md5_hash.hexdigest().upper()
                vaultdb_data['compressed-sha1'] = compressed_sha1_hash.hexdigest().upper()
                self.log.info('VaultDB (' + vaultdb_data['name'] + ') was successfully downloaded to ' + gzip_file)

                # To overcome current limits in the gzip module, let the caller decide if decomression should occur
                if decompress is True:
                    self.log.info('Decompressing the file...')
                    md5_hash = hashlib.md5()
                    sha1_hash = hashlib.sha1()
                    gz_db_file = gzip.open(gzip_file, 'rb')
                    with open(localpath, 'wb') as db_file:
                        decompress_continue_loop = True
                        while decompress_continue_loop:
                            filechunk = gz_db_file.read(file_chunk_size)
                            if len(filechunk) == 0:
                                decompress_continue_loop = False
                            else:
                                db_file.write(filechunk)
                                md5_hash.update(filechunk)
                                sha1_hash.update(filechunk)
                    gz_db_file.close()
                    self.log.info('VaultDB (' + vaultdb_data['name'] + ') in ' + gzip_file + ' was decompressed to ' + localpath)
                    vaultdb_data['md5'] = md5_hash.hexdigest().upper()
                    vaultdb_data['sha1'] = sha1_hash.hexdigest().upper()

                if meter['bytes-total'] > (5 * 1024 * 1024 * 1024):
                    large_file_hashes = self.__GetLargeFileHashes(localpath)
                    vaultdb_data['large-file'] = {}
                    vaultdb_data['large-file']['hashes'] = large_file_hashes['hashes']
                    vaultdb_data['large-file']['md5'] = large_file_hashes['md5']

                return True
        except LookupError:
            raise UserWarning('Invalid VaultDB Data provided.')

    def UploadVaultDb(self, container, vaultdb_data, localpath, skip_md5_check=False, compress=True, maximum_file_size_supported=(5 * 1024 * 1024 * 1024)):
        """
        Upload the VaultDB to CloudFiles from a local path
            container - the CloudFiles container in which to put the VaultDB
            vaultdb_data - the CloudFiles data reqgarding the VaultDB (see GetActiveDB() for details)
            localpath - the local path from which to read the VaultDB to upload
            skip_md5_check - enfoce that the detected MD5 matches the 'md5' in the vaultedb_data dictionary
            compress - whether or not to automatically compress the data into a gzip prior to upload

            Note: There is a bug in the gzip module that prevents a file larger than 2 GB from being compressed.
                When the VaultDB is larger than 2GB, then 'compress' needs to be false and the user needs to pre-compress.

        Requires the following entries in the 'vaultdb_data' parameter:
            - 'name' - the name within the container of the VaultDB file

        The following entries in the 'vaultdb_data' parameter are optional:
            - 'md5' - the MD5 of the data on disk, required if skip_md5_check is False

        Adds the following entries to the 'vaultdb_data' parameter:
            - 'upload-md5' - the MD5 of the data read from disk
            - 'upload-compressed-md5' - the MD5 of the compressed data
            - 'upload-bytes' - the number of bytes for the file on disk
            - 'upload-compressed-bytes' - the number of bytes for the compressed file sent to Cloud Files
        """
        self.apihost = self._get_container(container)
        file_chunk_size = 4 * 1024 * 1024
        try:
            md5_hash = hashlib.md5()
            gzip_file = None
            with open(localpath, 'rb') as db_file:

                if compress is True:

                    # Compress first
                    gzip_file = '{0:}.gz'.format(localpath)
                    with gzip.open(gzip_file, 'wb') as gz_db_file:
                        compress_continue_loop = True
                        while compress_continue_loop:
                            filechunk = db_file.read(file_chunk_size)
                            if len(filechunk) == 0:
                                compress_continue_loop = False
                            else:
                                gz_db_file.write(filechunk)
                                md5_hash.update(filechunk)
                else:
                    uncompressed_continue_loop = True
                    while uncompressed_continue_loop:
                        filechunk = db_file.read(file_chunk_size)
                        if len(filechunk) == 0:
                            break
                        else:
                            md5_hash.update(filechunk)
                    gzip_file = localpath

            if maximum_file_size_supported is not None:
                if int(os.path.getsize(gzip_file)) >= maximum_file_size_supported:
                    if gzip_file == localpath:
                        raise NotImplementedError('The VaultDB is larger than the presently supported file size.')
                    else:
                        raise NotImplementedError('The Compressed VaultDB is larger than the presently supported file size.')

            vaultdb_data['upload-md5'] = md5_hash.hexdigest().upper()
            if skip_md5_check is False:
                if md5_hash.hexdigest().upper() != vaultdb_data['md5']:
                    raise UserWarning('Unable to verify the data read for compression is what was expected to be passed in.')

            # Build an MD5 for the ETAG support in Cloud Files to guarantee that it has the file correctly
            gz_md5_hash = hashlib.md5()
            with open(gzip_file, 'rb') as compressed_data:
                md5_continue_loop = True
                while md5_continue_loop:
                    filechunk = compressed_data.read(file_chunk_size)
                    if len(filechunk) == 0:
                        break
                    else:
                        gz_md5_hash.update(filechunk)
            vaultdb_data['upload-compressed-md5'] = gz_md5_hash.hexdigest().upper()
            vaultdb_data['upload-compressed-md5-actual'] = vaultdb_data['upload-compressed-md5']

            # Cloud Files requires we split up based on 5 GB limits
            if os.path.getsize(gzip_file) > 5 * 1024 * 1024 * 1024:
                large_file_hashes = self.__GetLargeFileHashes(localpath)
                vaultdb_data['upload-large-file'] = {}
                vaultdb_data['upload-large-file']['hashes'] = large_file_hashes['hashes']
                vaultdb_data['upload-large-file']['md5'] = large_file_hashes['md5']

                # This becomes the Etag
                vaultdb_data['upload-compressed-md5'] = vaultdb_data['upload-large-file']['md5']

                # 512 MB boundaries
                vaultdb_data['upload-split-boundary'] = 512 * 1024 * 1024

            # Retrieve the size in bytes of the data files - compressed and uncompressed
            vaultdb_data['upload-bytes'] = os.path.getsize(localpath)
            vaultdb_data['upload-compressed-bytes'] = os.path.getsize(gzip_file)

            # Set the ETag header to guarantee that the object is written correctly to multiple nodes in
            # Cloud Files. Otherwise Cloud Files may truncate the object thus causing the hash to be different that
            # the file we have on disk. We still need to verify it later, but this should guarantee that check will pass
            self.ReInit(self.sslenabled, '/' + vaultdb_data['name'])
            self.headers['X-Auth-Token'] = self.authenticator.AuthToken
            self.headers['ETag'] = vaultdb_data['upload-compressed-md5']
            self.headers['Content-Type'] = 'application/octet-stream'
            self.headers['Content-Length'] = str(vaultdb_data['upload-compressed-bytes'])
            self.log.debug('uri: %s', self.Uri)
            self.log.debug('headers: %s', self.Headers)

            # TODO:
            # >5GB File upload support:
            #   - add extra header line (see Cloud Backup Agent for details)
            #   - split file into 512MB chunks and upload each
            #   - generate a manifest file for Cloud Files to make them into a 'large file' object in the container

            # Attempt the upload
            with open(gzip_file, 'rb') as upload_data:
                res = requests.put(self.Uri, headers=self.Headers, data=upload_data)

            # Chek the result
            if res.status_code in (200, 201):

                # Verify Cloud Files thinks it has the same data we think we have
                if res.headers['ETag'].upper() == vaultdb_data['upload-compressed-md5']:
                    return True
                else:
                    # We disagree on content! :(
                    UserWarning('Failed to verify the uploaded data matched the compressed data on disk - {0:} vs {1:}.'.format(res.headers['ETag'].upper(), vaultdb_data['upload-compressed-md5']))

            else:
                # Upload failed
                raise UserWarning('Error while uploading compressed version of {0:} to {1:}. Error Code: {2:} Text: {3:}'.format(localpath, self.Uri, res.status_code, res.text))

        except LookupError:
            # Something cause a dictionary lookup failure...
            raise UserWarning('Invalid VaultDB Data provided.')

    def CheckBundleDigest(self, container, uripath, bundle_data):
        """
        Download the Bundle from CloudFiles into a local path
            container - the CloudFiles container in which to find the Vault DB
            bundle_data - a dict containing atlest the 'id'  and 'md5' of the bundle
            localpath - the local path at which to store the downloaded VaultDB
        """
        self.apihost = self._get_container(container)
        try:
            fulluri = uripath + '/BUNDLES/' + bundle_data['name']
            self.ReInit(self.sslenabled, '/' + fulluri)
            self.headers['X-Auth-Token'] = self.authenticator.AuthToken
            self.log.debug('uri: %s', self.Uri)
            self.log.debug('headers: %s', self.Headers)
            try:
                res = requests.head(self.Uri, headers=self.Headers)
            except requests.exceptions.SSLError as ex:
                self.log.error('Requests SSLError: {0}'.format(str(ex)))
                res = requests.head(self.Uri, headers=self.Headers, verify=False)
            if res.status_code == 404:
                raise UserWarning('Server failed to find the specified bundle')
            elif res.status_code >= 300:
                raise UserWarning('Server responded unexpectedly during download (Code: ' + str(res.status_code) + ' )')
            else:
                digest = res.headers['etag'].upper()
                result = (digest == bundle_data['md5'])
                self.log.debug('CloudFiles Bundle Digest (' + digest + ') == Bundle MD5 (' + bundle_data['md5'] + ')? ' + str(result))
                return result
        except LookupError:
            raise UserWarning('Invalid VaultDB Data provided.')

    # TODO: Test
    def DownloadBundle(self, container, uripath, bundle_data, localpath):
        """
        Download the Bundle from CloudFiles into a local path
            container - the CloudFiles container in which to find the Vault DB
            bundle_data - a dict containing atlest the 'id'  and 'md5' of the bundle
            localpath - the local path at which to store the downloaded VaultDB

        Note: Adds 'download-md5' and 'download-sha1' entries to the bundle_data
        """
        self.apihost = self._get_container(container)
        try:
            fulluri = uripath + '/BUNDLES/' + '{0:010}'.format(bundle_data['id'])
            self.ReInit(self.sslenabled, '/' + fulluri)
            self.headers['X-Auth-Token'] = self.authenticator.AuthToken
            self.log.debug('uri: %s', self.Uri)
            self.log.debug('headers: %s', self.Headers)
            try:
                res = requests.get(self.Uri, headers=self.Headers)
            except requests.exceptions.SSLError as ex:
                self.log.error('Requests SSLError: {0}'.format(str(ex)))
                res = requests.get(self.Uri, headers=self.Headers, verify=False)
            if res.status_code == 404:
                raise UserWarning('Server failed to find the specified bundle')
            elif res.status_code >= 300:
                raise UserWarning('Server responded unexpectedly during download (Code: ' + str(res.status_code) + ' )')
            else:
                meter = {}
                meter['bytes-remaining'] = int(res.headers['Content-Length'])
                meter['bar-count'] = 50
                meter['bytes-per-bar'] = meter['bytes-remaining'] // meter['bar-count']
                meter['block-size'] = min(4 * 1024 * 1024, meter['bytes-per-bar'])
                meter['chunks-per-bar'] = meter['bytes-per-bar'] // meter['block-size']
                meter['chunks'] = 0
                meter['bars-remaining'] = meter['bar-count']
                meter['bars-completed'] = 0
                self.log.info('Downloading bundle: {0} bytes...'.format(meter['bytes-remaining']))
                self.log.info('[' + ' ' * meter['bar-count'] + ']')
                bundle_file = localpath + '.bundle-{0:010}'.format(bundle_data['id'])
                md5_hash = hashlib.md5()
                sha1_hash = hashlib.sha1()
                with open(bundle_file, 'wb') as bundle_on_disk:
                    for bundle_chunk in res.iter_content(chunk_size=meter['block-size']):
                        bundle_on_disk.write(bundle_chunk)
                        md5_hash.update(bundle_chunk)
                        sha1_hash.update(bundle_chunk)
                        meter['chunks'] += 1
                        if meter['chunks'] == meter['chunks-per-bar']:
                            meter['chunks'] = 0
                            meter['bars-completed'] += 1
                            meter['bars-remaining'] -= 1
                            self.log.info('[' + '-' * meter['bars-completed'] + ' ' * meter['bars-remaining'] + ']')
                bundle_data['download-md5'] = md5_hash.hexdigest().upper()
                bundle_data['download-sha1'] = sha1_hash.hexdigest().upper()
                self.log.info('Bundle (' + bundle_data['id'] + ') was successfully downloaded to ' + bundle_file)
                bundle_data['file-on-disk'] = bundle_file
                return True
        except LookupError:
            raise UserWarning('Invalid VaultDB Data provided.')

    # TODO: Test
    def GetFile(self, uri, uripath, localpath):
        """
        Download the VaultDB
            uri - uri in CloudFiles to download as source
            localpath - local uri for destination
        """
        self.apihost = self._get_container(uri)
        self.ReInit(self.sslenabled, uripath)
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.log.debug('headers: %s', self.Headers)
        try:
            res = requests.get(self.Uri, headers=self.Headers)
        except requests.exceptions.SSLError as ex:
            self.log.error('Requests SSLError: {0}'.format(str(ex)))
            res = requests.get(self.Uri, headers=self.Headers, verify=False)
        return res.status_code

    # TODO: Test
    def GetCloudFile(self, uriserver, uripath):
        """
        Access a file in the user's CloudFile account - not a backup agent file (apparently)
        """
        self.apihost = self._get_container(uriserver)
        self.ReInit(self.sslenabled, '/v1/' + str(self.authenticator.AuthId) + '/' + uripath + '/DB')
        self.headers['X-Auth-Token'] = self.authenticator.AuthToken
        self.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        self.headers['Accept'] = 'application/json'  # Retrieve is in JSON format
        self.log.debug('uri: %s', self.Uri)
        self.log.debug('uri: %s', self.Uri)
        self.log.debug('headers: %s', self.Headers)
        try:
            res = requests.get(self.Uri, headers=self.Headers)
        except requests.exceptions.SSLError as ex:
            self.log.error('Requests SSLError: {0}'.format(str(ex)))
            res = requests.get(self.Uri, headers=self.Headers, verify=False)
        if res.status_code == 200:
            self.log.debug('Content is available')
            return True
        elif res.status_code == 204:
            self.log.debug('No content available.')
            return False
        else:
            self.log.error('Error retrieving data (' + str(res.status_code) + ') - ' + res.text)
            return False
