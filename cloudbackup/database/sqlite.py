"""
Rackspace Cloud Backup SQLite Database Functionality
"""
from __future__ import print_function

import base64
import datetime
import logging
import os
import os.path
import random
import sqlite3


class CloudBackupCleanUpOffset(object):

    MAX_CLEANUP_OFFSET = int(datetime.timedelta(weeks=1).total_seconds())
    INVALID_CLEANUP_OFFSET = (MAX_CLEANUP_OFFSET + 1)

    KEEP_EXPIRED_FILES_FOREVER = 0
    CLEANUP_INDEX_NEVER_DELETE = 1999999999

    @classmethod
    def random_index(cls):
        """Generate a new Random Offset Value

        :returns: int - random value where 0 <= v <= MAX_CLEANUP_OFFSET
        """
        return random.randint(0, cls.MAX_CLEANUP_OFFSET)

    @classmethod
    def make_new_valid_offset(cls, offset, seconds):
        """Calculate a new offset value based on an existing offset and the number of seconds to change it by

        :returns: int - number of seconds the offset adds to the base time
        """
        o = CloudBackupCleanUpOffset(offset=offset)
        if (o.offset == cls.INVALID_CLEANUP_OFFSET):
            raise ValueError('Offset is not modifiable at this time. Please set a modifiable offset first.')

        # Enforce that the new offset must be a valid offset value
        if o.offset == cls.INVALID_CLEANUP_OFFSET:
            o.offset = cls.MAX_CLEANUP_OFFSET

        if(o.offset + seconds) < 0:
            raise ValueError('Offset will go below the minimum value. Please adjust forward in time.')

        return int((o.offset + seconds) % cls.MAX_CLEANUP_OFFSET)

    @classmethod
    def get_next_cleanup_time(cls, offset, daysToKeepOldVersions, adjustment=None):
        """Calculate the next cleanup week

        (Current Time (Unix Epoch) + (mDaysToKeepFiles * Seconds Per Day) + Offset) / Seconds Per Week
        """
        cleanup_week = None
        weekday = None

        if daysToKeepOldVersions is cls.KEEP_EXPIRED_FILES_FOREVER:
            cleanup_week = cls.CLEANUP_INDEX_NEVER_DELETE

        elif not isinstance(offset, CloudBackupCleanUpOffset):
            raise TypeError('offset must be an instance of CloudBackupCleanUpOffset')

        elif not ((adjustment is None) or isinstance(adjustment, datetime.timedelta)):
            raise TypeError('adjustment must be none or  must be an instance of datetime.timedelta')

        else:
            current_time = datetime.datetime.utcnow()
            adjust_by_days = datetime.timedelta(days=daysToKeepOldVersions)
            adjust_offset = datetime.timedelta(seconds=offset.offset)

            new_time = current_time + adjust_by_days + adjust_offset
            if adjustment is not None:
                new_time = new_time + adjustment

            # Convert to ISO representation
            iso_cal = new_time.isocalendar()

            # ISO Week of the current year
            current_week = iso_cal[1]

            # Number of weeks since Jan 1, 1970
            weeks_offset = (iso_cal[0] - 1970) * 52

            # Cleanup Week is # of weeks since 1970
            cleanup_week = current_week + weeks_offset

            # offset.offset is really just a Unix Epoch offset,
            # so treat it as a Unix Epoch to determine which day of the week starts
            # the cleanup week for this agent
            weekday = datetime.datetime.fromtimestamp(offset.offset).strftime('%A - %H:%M:%S UTC')

        return (cleanup_week, weekday)

    @staticmethod
    def getInvalidOffset():
        """Create a new offset with the invalid offset set

        :returns: CloudBackupCleanUpOffset with the new offset
        """
        return CloudBackupCleanUpOffset(offset=CloudBackupCleanUpOffset.INVALID_CLEANUP_OFFSET)

    @staticmethod
    def getRandomOffset():
        """Create a new offset with the random offset set

        :returns: CloudBackupCleanUpOffset with the new offset
        """
        return CloudBackupCleanUpOffset(offset=CloudBackupCleanUpOffset.random_index())

    def __init__(self, offset=None):
        """Initialize the cleanup offset

        :param offset: int or CloudBackupCleanUpOffset - the cleanup offset being represented
        :raises: TypeError - if offset is not an instance of int or CloudBackupCleanUpOffset
        """

        # if in then just store it
        if isinstance(offset, int):
            self._offset = offset
            self.validate_offset()

        # If CloudBackupCleanUpOffset then copy the offset over
        elif isinstance(offset, CloudBackupCleanUpOffset):
            offset.validate_offset()
            self._offset = offset.offset

        # Otherwise we don't support the conversion
        else:
            raise TypeError('Unknown offset type {0:}'.format(offset.__class__))

    def validate_offset(self):
        """Enforce that the stored offset is within the valid values

        :raises: ValueError when the value exceeds the limit of 0 <= v <= INVALID_CLEANUP_INDEX
        """
        if self._offset < 0 or self._offset > self.__class__.INVALID_CLEANUP_OFFSET:
            raise ValueError('offset must be in a range between 0 and {0:}'.format(self.__class__.INVALID_CLEANUP_OFFSET))

    @property
    def offset(self):
        """Offset being stored

        :returns: int - number of seconds the offset adds to the base time
        """
        if self._offset is None:
            return self.__class__.INVALID_CLEANUP_OFFSET
        else:
            return self._offset

    @offset.setter
    def offset(self, offset):
        """Update the stored offset to a new, specific value
        """
        self._offset = offset
        self.validate_offset()

    def changeBy(self, seconds=None):
        """Modify the stored offset by the specified number of seconds

        :raises: ValueError - when the new value is not valid
        """
        if self._offset is None:
            raise ValueError('Offset is not modifiable at this time. Please set a modifiable offset first.')

        old_offset = self._offset
        try:
            self._offset = self._offset + seconds
            self.validate_offset()
            return True

        except ValueError:
            self._offset = old_offset
            raise ValueError('Seconds ({1:}) cannot make offset go below zero (0) or above {0:}'.format(self.__class__.INVALID_CLEANUP_OFFSET, seconds))


class CloudBackupSqlite(object):
    """
    Cloud Backup Sqlite Database Interface
    """

    def __init__(self, dbfile):
        """
        Open a SQLite3 instance to the specified sqlite3 db file
        """
        self.log = logging.getLogger(__name__)
        self.dbfile = dbfile
        self.dbinstance = None
        self.__open_db()

    def __del__(self):
        """
        Clean up
        """
        self.__close_db()

    def __open_db(self):
        """
        Open the database
        """
        self.log.debug('Opening database')
        self.dbinstance = sqlite3.connect(self.dbfile)
        self.dbinstance.text_factory = str

    def __close_db(self):
        """
        Close the database instance
        """
        self.log.debug('Closing database')
        self.dbinstance.close()
        del self.dbinstance
        self.dbinstance = None

    def __is_db_opened(self):
        """
        Return whether or not the database is currently opened for use
        """
        self.log.debug('Checking open: {0:}'.format((self.dbinstance is not None)))
        return (self.dbinstance is not None)

    def GetDirectoryPath(self, directoryid):
        """
        Given a directory id from the database, retrieve its path and parent directory id
        """
        conn = self.dbinstance.cursor()
        conn.execute('SELECT parentdirectoryid, path FROM directories WHERE directoryid=:id', {'id': directoryid})
        results = conn.fetchone()
        self.log.debug('     directoryid(%d) has parentdirectoryid:%d and path:%s' % (directoryid, results[0], results[1]))
        return results

    def GetFilenameSet(self, snapshotid):
        """
        Given a snapshotid return all the files and their relevant data from the database
            snapshotid - id value maching the snapshots table for a valid snapshot
        """
        conn = self.dbinstance.cursor()
        # note: we have to check against two snapshot id's as there is the possibility that no file has the snapshot id
        #   that was provided if that file is still in the latest snapshot and therefore fresh.
        #   Not sure how else to associate the files to a specific snapshot ftm.
        results = {}
        results['filedata'] = {}
        files = set()
        for row in conn.execute('SELECT fileid FROM files WHERE digest IS NOT NULL AND (lastsnapshotid=:snapshotid or lastsnapshotid=2000000000)', {'snapshotid': snapshotid}):
            files.add(row[0])
        return files

    def GetFileInformation(self, fileid):
        """
        Given a fileid return all the files and their relevant data from the database

        Returns a dictionary containing the following:
            filedata
                path
                    name
                    sha512
                    size
                    blockdata (for when size is below a given threshold)
                    blocks
                        dictionary containing:
                            id
                            sha512
                            size
                            bundle (dictionary containing id and offset)
                    bundles
                        set() - list of bundles that go with the file
            bundles
                set() - list of unique bundles that go with the all files returned
        """
        conn = self.dbinstance.cursor()
        # note: we have to check against two snapshot id's as there is the possibility that no file has the snapshot id
        #   that was provided if that file is still in the latest snapshot and therefore fresh.
        #   Not sure how else to associate the files to a specific snapshot ftm.
        results = {}
        results['filedata'] = []
        bundledata = set()
        # Should only run once...
        for row in conn.execute('SELECT directories.path, files.filename, files.digest, files.size, files.fileid, files.blockdata FROM files, directories WHERE digest IS NOT NULL AND files.directoryid=directories.directoryid AND files.fileid=:fileid', {'fileid': fileid}):
            self.log.debug('%s/%s has SHA1 %s and is %u bytes' % (row[0], row[1], row[2], row[3]))
            # Get the file specific block data
            blockdata = self.GetFileBlocks(row[4])
            # Build up the data we're returning
            filepath = row[0] + '/' + row[1]
            filedata = {}
            filedata['name'] = filepath
            filedata['base64-sha512'] = row[2].upper()
            filedata['sha512'] = base64.b16encode(base64.b64decode(row[2])).upper()
            filedata['size'] = row[3]
            filedata['blockdata'] = row[5]
            filedata['blocks'] = blockdata['blocks']
            filedata['bundles'] = blockdata['bundles']
            results['filedata'].append(filedata)

            if not len(blockdata['bundles']):
                self.log.debug('\tblock data:\n\"\"\"\n%s\n\"\"\"' % row[5])
            else:
                # Added the bundle data back to the main set - we only want one copy of each bundle
                for bundleid in blockdata['bundles']:
                    bundledata.add(bundleid)

        # now that we're done capturing all the file specific data, we can now capture the bundle data
        results['bundles'] = self.GetFileBundles(bundledata)
        self.log.debug(results['bundles'])
        return results

    def GetFilenames(self, snapshotid):
        """
        Given a snapshotid return all the files contained in it and their relevant data from the database

        Returns a dictionary containing the following:
            filedata
                path
                    name
                    sha512
                    size
                    blockdata (for when size is below a given threshold)
                    blocks
                        dictionary containing:
                            id
                            sha512
                            size
                            bundle (dictionary containing id and offset)
                    bundles
                        set() - list of bundles that go with the file
            bundles
                set() - list of unique bundles that go with the all files returned
        """
        conn = self.dbinstance.cursor()
        # note: we have to check against two snapshot id's as there is the possibility that no file has the snapshot id
        #   that was provided if that file is still in the latest snapshot and therefore fresh.
        #   Not sure how else to associate the files to a specific snapshot ftm.
        results = {}
        results['filedata'] = []
        bundledata = set()
        for row in conn.execute('SELECT directories.path, files.filename, files.digest, files.size, files.fileid, files.blockdata FROM files, directories WHERE digest IS NOT NULL AND files.directoryid=directories.directoryid AND (files.lastsnapshotid=:snapshotid or files.lastsnapshotid=2000000000) and files.backupconfigurationid = (select backupconfigurationid from snapshots where snapshotid=:snapshotid)', {'snapshotid': snapshotid}):
            self.log.debug('%s/%s has SHA512 %s and is %u bytes' % (row[0], row[1], row[2], row[3]))
            # Get the file specific block data
            blockdata = self.GetFileBlocks(row[4])
            # Build up the data we're returning
            filepath = row[0] + '/' + row[1]
            filedata = {}
            filedata['name'] = filepath
            filedata['base64-sha512'] = row[2].upper()
            filedata['sha512'] = base64.b16encode(base64.b64decode(row[2])).upper()
            filedata['size'] = row[3]
            filedata['blockdata'] = row[5]
            filedata['blocks'] = blockdata['blocks']
            filedata['bundles'] = blockdata['bundles']
            results['filedata'].append(filedata)
            if not len(blockdata['bundles']):
                self.log.debug('\tblock data:\n\"\"\"\n%s\n\"\"\"' % row[5])
            else:
                # Added the bundle data back to the main set - we only want one copy of each bundle
                for bundleid in blockdata['bundles']:
                    bundledata.add(bundleid)

        # now that we're done capturing all the file specific data, we can now capture the bundle data
        results['bundles'] = self.GetFileBundles(bundledata)
        self.log.debug(results['bundles'])
        return results

    def GetFileBlocks(self, fileid):
        """
        Given a fileid retrieve all the associated block information

        Returns a dictionary containing the following:
            blocks
                dictionary containing:
                    id
                    sha1
                    size
                    bundle (dictionary containing id and offset)
            bundles
                set() - list of bundles that go with the file
        """
        conn = self.dbinstance.cursor()
        blocks = {}
        bundles = set()
        for row in conn.execute('SELECT fileblocks.idx, blocks.blockid, blocks.sha1, blocks.size, blocks.bundleid, blocks.bundleoffset FROM fileblocks,blocks WHERE fileblocks.fileid=:fileid AND blocks.blockid=fileblocks.blockid ORDER BY fileblocks.idx', {'fileid': fileid}):
            blocks[row[0]] = {}
            blocks[row[0]]['id'] = row[1]
            blocks[row[0]]['sha1'] = row[2].upper()
            blocks[row[0]]['size'] = row[3]
            blocks[row[0]]['bundle'] = {}
            blocks[row[0]]['bundle']['id'] = row[4]
            blocks[row[0]]['bundle']['offset'] = row[5]
            bundles.add(row[4])

        self.log.debug('\tfileid(' + str(fileid) + ') has blocks ' + str(blocks))

        results = {}
        results['blocks'] = blocks
        results['bundles'] = bundles
        return results

    def GetFileBundles(self, bundleids):
        """
        Given a bundle list retrieve all the information

        Returns a dictionary of bundle is containins the following:
            id
            md5
            totalsize
            garbagesize
            usedsized
        """
        conn = self.dbinstance.cursor()
        bundles = []
        for bundleid in bundleids:
            for row in conn.execute('SELECT md5, totalsize, garbagesize FROM bundles WHERE bundleid=:bundleid', {'bundleid': bundleid}):
                bundledata = {}
                bundledata['id'] = bundleid
                bundledata['name'] = '{0:010}'.format(bundleid)
                bundledata['md5'] = row[0].upper()
                bundledata['totalsize'] = row[1]
                bundledata['garbagesize'] = row[2]
                bundledata['usedsize'] = (row[1] - row[2])
                bundles.append(bundledata)
        return bundles

    def GetFileAddedInSnapshot(self, snapshotid, limit_lower=None, limit_higher=None):
        """
        Given a snapshot id, retrieve basic file information from the files table

        Returns a list of dictionaries.
        Each dictionary contains:
            id
            directoryid
            directory -- directory path
            filename
            type -- 1 folder, 0 file, 2 symlink
        """
        conn = self.dbinstance.cursor()
        stmt = 'SELECT f.fileid, f.directoryid, d.path, f.filename, f.type, ' \
               'f.metadata FROM files f ' \
               'JOIN directories d  ON f.directoryid=d.directoryid ' \
               'WHERE addedinsnapshotid =: snapshotid '\
               'ORDER BY d.path'

        stmt_dict = {
            'snapshotid': snapshotid
        }

        if limit_lower:
            stmt = '{0:} AND f.filename >= :lower_limit'.format(stmt)
            stmt_dict['limit_lower'] = limit_lower

        if limit_higher:
            stmt = '{0:} AND f.filename < :higher_limit'.format(stmt)
            stmt_dict['limit_higher'] = limit_higher

        stmt = '{0:} ORDER BY d.path'.format(stmt)
        print('SQL: {0:}'.format(stmt))

        results = list()
        for row in conn.execute(stmt, {'snapshotid': snapshotid}):
            fileInfo = dict()
            fileInfo['id'] = row[0]
            fileInfo['directoryid'] = row[1]
            fileInfo['directory'] = row[2]
            fileInfo['filename'] = row[3]
            fileInfo['type'] = row[4]
            fileInfo['metadata'] = row[5]
            results.append(fileInfo)
        return results

    def GetBackupConfigurations(self):
        """
        Returns the list of existing backup configurations
        """
        conn = self.dbinstance.cursor()

        backupconfigurations = []

        for result in conn.execute('SELECT backupconfigurationid, legacyguid, externalid, cleanupdays, removed FROM backupconfigurations'):
            backupconfiguration = {
                'backupconfigurationid': int(result[0]),
                'legacyguid': result[1],
                'externalid': int(result[2]),
                'cleanupdays': int(result[3]),
                'removed': int(result[4])
            }
            backupconfigurations.append(backupconfiguration)

        return backupconfigurations

    def GetExternalBackupConfigurationId(self, backupconfigurationid):
        """
        Given a backup configuration id used internally by the agent return its equivalent for the API
        """
        conn = self.dbinstance.cursor()
        result = conn.execute('SELECT externalid FROM backupconfigurations WHERE backupconfigurationid=:backupconfigurationid', {'backupconfigurationid': backupconfigurationid})
        data = result.fetchone()
        return data[0]

    def GetInternalBackupConfigurationId(self, backupconfigurationid):
        """
        Given a backup configuration id used externally by the API return its equivalent for the agent
        """
        conn = self.dbinstance.cursor()
        result = conn.execute('SELECT backupconfigurationid FROM backupconfigurations WHERE externalid=:backupconfigurationid', {'backupconfigurationid': backupconfigurationid})
        data = result.fetchone()
        return data[0]

    def DetectUniqueConstraintViolations(self):
        """
        Detect the database entries that create a unique constraint violation

        Returns: True/False for whether or not the Unique Constraint Violation was detected
        """
        conn = self.dbinstance.cursor()
        conn2 = self.dbinstance.cursor()
        results = list()
        results.append(0)

        self.log.debug('Checking for unique constraint errors...')
        for entry in conn.execute('SELECT COUNT(fileid), backupconfigurationid, directoryid, filename, addedinsnapshotid, lastsnapshotid FROM files WHERE lastsnapshotid=2000000000 GROUP BY filename, directoryid, backupconfigurationid HAVING COUNT(fileid) > 1'):

            info = {
                'count': entry[0],
                'backupconfigurationid': entry[1],
                'directoryid': entry[2],
                'filename': entry[3],
                'addedinsnapshotid': entry[4],
                'lastsnapshotid': entry[5]
            }

            self.log.debug('Found entry (directoryid={0:}, filename={1:}, backupconfigurationid={2:}: added-in={3:}, count={4:}) with possible errors'
                           .format(info['directoryid'], info['filename'], info['backupconfigurationid'], info['addedinsnapshotid'], info['count']))
            # Reset the addedinsnapshot for each round
            first_round = True

            # Retrieve all invalid rows from the database for the provided entry
            for row in conn2.execute('SELECT directoryid, fileid, filename, addedinsnapshotid, lastsnapshotid, backupconfigurationid FROM files WHERE directoryid = ? AND filename = ? AND backupconfigurationid = ? AND lastsnapshotid = ? ORDER BY addedinsnapshotid DESC',
                                     (info['directoryid'], info['filename'], info['backupconfigurationid'], info['lastsnapshotid'])):

                confirmed_info = {
                    'directoryid': row[0],
                    'fileid': row[1],
                    'filename': row[2],
                    'addedinsnapshotid': row[3],
                    'lastsnapshotid': row[4],
                    'backupconfigurationid': row[5]
                }

                # First round we just want the snapshotid
                # All remaining rounds we update the lastsnapshotid field to be the added in snapshotid of the previous round
                if not first_round:
                    self.log.debug('Confirmed entry (directoryid={0:}, filename={1:}, backupconfigurationid={2:}) has errors'
                                   .format(confirmed_info['directoryid'], confirmed_info['filename'], confirmed_info['backupconfigurationid']))
                    results[0] = results[0] + 1

                first_round = False

        if results[0] == 0:
            results.pop()

        return results

    def DetectUnicodeDirectoryNameErrors(self):
        """
        Detect if any directory names are in violation of the ASCII characters
        """
        conn = self.dbinstance.cursor()
        results = list()

        self.log.debug('Checking for ASCII errors in directory names...')
        for entry in conn.execute('SELECT directoryid, path FROM directories'):
            path_id = int(entry[0])
            path = entry[1]
            for v in path:
                if ord(v) > 128:
                    self.log.debug('Error with directory name. Directory ID = {0:}'.format(path_id))
                    results.append((path_id, path))
                    break

        return results

    def DetectUnicodeFileNameErrors(self):
        """
        Detect if any file names are in violation of the ASCII characters
        """
        conn = self.dbinstance.cursor()
        results = list()

        self.log.debug('Checking for ASCII errors in directory names...')
        for entry in conn.execute('SELECT fileid, filename FROM files'):
            file_id = int(entry[0])
            filename = entry[1]
            for v in filename:
                if ord(v) > 128:
                    self.log.debug('Error with file name. File ID = {0:}'.format(file_id))
                    results.append((file_id, filename))
                    break

        return results

    def GetDirectory(self, directoryid):
        """
        Return the directory associated with the specified directoryid
        """
        conn = self.dbinstance.cursor()

        results = conn.execute('SELECT path FROM directories WHERE directoryid == {0:}'.format(directoryid))
        directory = results.fetchone()
        return directory[0]

    def FixUniqueConstraintViolations(self, unique_constraint_rows):
        """
        Fix the Unique Constraint Violations
        """
        conn = self.dbinstance.cursor()
        conn2 = self.dbinstance.cursor()
        conn3 = self.dbinstance.cursor()
        commit_database = False

        self.log.debug('Checking for unique constraint errors...')
        for entry in conn.execute('SELECT COUNT(fileid), backupconfigurationid, directoryid, filename, addedinsnapshotid, lastsnapshotid FROM files WHERE lastsnapshotid=2000000000 GROUP BY filename, directoryid, backupconfigurationid HAVING COUNT(fileid) > 1'):

            info = {
                'count': entry[0],
                'backupconfigurationid': entry[1],
                'directoryid': entry[2],
                'filename': entry[3],
                'addedinsnapshotid': entry[4],
                'lastsnapshotid': entry[5]
            }

            self.log.debug('Found entry (directoryid={0:}, filename={1:}, backupconfigurationid={2:}: added-in={3:}, count={4:}) with possible errors'
                           .format(info['directoryid'], info['filename'], info['backupconfigurationid'], info['addedinsnapshotid'], info['count']))

            # Reset the addedinsnapshot for each round
            first_round = True

            # Retrieve all invalid rows from the database for the provided entry
            for row in conn2.execute('SELECT directoryid, fileid, filename, addedinsnapshotid, lastsnapshotid, backupconfigurationid FROM files WHERE directoryid = ? AND filename = ? AND backupconfigurationid = ? AND lastsnapshotid = ? ORDER BY addedinsnapshotid DESC',
                                     (info['directoryid'], info['filename'], info['backupconfigurationid'], info['lastsnapshotid'])):

                confirmed_info = {
                    'directoryid': row[0],
                    'fileid': row[1],
                    'filename': row[2],
                    'addedinsnapshotid': row[3],
                    'lastsnapshotid': row[4],
                    'backupconfigurationid': row[5]
                }

                # First round we just want the snapshotid
                # All remaining rounds we update the lastsnapshotid field to be the added in snapshotid of the previous round
                if not first_round:
                    self.log.debug('Fixing entry (directoryid={0:}, filename={1:}, backupconfigurationid={2:}) - lastsnapshotid ({3:} -> {4:})'
                                   .format(confirmed_info['directoryid'], confirmed_info['filename'], confirmed_info['backupconfigurationid'], confirmed_info['lastsnapshotid'], confirmed_info['addedinsnapshotid']))
                    conn3.execute('UPDATE files SET lastsnapshotid = ? WHERE directoryid = ? AND filename = ? AND addedinsnapshotid = ? AND lastsnapshotid = ? AND backupconfigurationid = ?',
                                  (confirmed_info['addedinsnapshotid'], confirmed_info['directoryid'], confirmed_info['filename'], confirmed_info['addedinsnapshotid'], confirmed_info['lastsnapshotid'], confirmed_info['backupconfigurationid']))
                    commit_database = True

                first_round = False

        if commit_database is True:
            self.dbinstance.commit()

        return True

    def ResetAgentCleanUpOffset(self):
        """
        Returns the Cleanup Offset to the default value which will cause the agent to generate a new random
        time for the cleanup offset to occur at.
        """
        new_offset = CloudBackupCleanUpOffset.getInvalidOffset()
        self.ChangeAgentCleanUpOffset(cleanup_offset=new_offset)

    def GetAgentCleanUpOffset(self):
        """
        Retrieves the Cleanup Offset from the database and returns an CloudBackupCleanUpOffset object containing the result.
        """
        conn = self.dbinstance.cursor()
        results = conn.execute('SELECT intvalue FROM keyvalues WHERE key="cleanupoffset"')

        result = results.fetchone()
        return CloudBackupCleanUpOffset(offset=int(result[0]))

    def SetAgentCleanUpOffset(self, cleanup_offset=CloudBackupCleanUpOffset.getRandomOffset()):
        """
        Sets the Cleanup Offset into the database based on the provided CloudBackupCleanUpOffset object
        """
        if isinstance(cleanup_offset, CloudBackupCleanUpOffset):
            if isinstance(cleanup_offset.offset, int):

                conn = self.dbinstance.cursor()
                conn.execute('INSERT OR REPLACE INTO keyvalues (key, intvalue) VALUES (?, ?)', ('cleanupoffset', cleanup_offset.offset))
                self.dbinstance.commit()

                return True

            else:
                raise TypeError('Cleanup Offset must be an integer type')

        else:
            raise TypeError('cleanup_offset must be an instance of CloudBackupCleanUpOffset')

    def GetAgentLastCleanUpWeek(self):
        """
        Retrieves the Last Cleanup Week from the database and returns as an integer
        """
        conn = self.dbinstance.cursor()
        results = conn.execute('SELECT intvalue FROM keyvalues WHERE key="lastcleanupindex"')

        result = results.fetchone()
        return int(result[0])

    def GetAgentNextCleanupsForConfigurations(self, cleanup_offset=None, adjustment=None):
        """
        Calculate the next cleanup time for each configuration in the database

        :param cleanup_offset: CloudBackupCleanUpOffset - the cleanup offset to use for the calculation
        :returns: a list of the configurations and their next cleanup information
                  each entry is a tuple of ( backupconfigurationid, cleanup week index, day of week that starts the cleanup week)
        """
        if cleanup_offset is None:
            cleanup_offset = self.GetAgentCleanUpOffset()

        conn = self.dbinstance.cursor()
        results = conn.execute('SELECT backupconfigurationid, cleanupdays FROM backupconfigurations')

        cleanup_times = []

        for backupconfig_result in results:
            backupconfigid = backupconfig_result[0]
            cleanup_days = int(backupconfig_result[1])

            next_cleanup_time = CloudBackupCleanUpOffset.get_next_cleanup_time(cleanup_offset, cleanup_days, adjustment=adjustment)

            data = (backupconfigid, next_cleanup_time[0], next_cleanup_time[1])

            cleanup_times.append(data)

        return cleanup_times

    def AddSnapshot(self, old_snapshots=None):
        """
        Insert new snapshot id(s).

        If oldsnapshots is None, then it detects the maximum snapshot id and replicates it alone.

        Parameters:
            oldsnapshots - None or an iterable containing the snapshotids to replicate with new snapshotids
        """
        conn = self.dbinstance.cursor()

        # If no old snapshotid was specified, then find the maximum one in the database
        if old_snapshots is None:
            max_existing_snapshot_results = conn.execute('SELECT MAX(snapshotid) FROM snapshots')
            max_existing_snapshot = max_existing_snapshot_results.fetchone()
            old_snapshots = list()
            old_snapshots.append(max_existing_snapshot[0])

        # Keep a list of the new snapshotids so we can return the maximum one, useful for the Caller for uploads to CloudFiles
        new_snapshots = list()
        for snapshot in old_snapshots:

            # Each new snapshot needs to be after the maximum entry in the table
            max_existing_snapshot_results = conn.execute('SELECT MAX(snapshotid) FROM snapshots')
            max_existing_snapshot = max_existing_snapshot_results.fetchone()
            new_snapshot_id = int(max_existing_snapshot[0]) + 1

            # Insert a new snapshot into the database using an existing snapshot as a baseline for certain values
            conn.execute('INSERT INTO snapshots (snapshotid, startdate, state, cleanupindex, backupconfigurationid) SELECT {0:}, startdate, 4, cleanupindex, backupconfigurationid FROM snapshots WHERE snapshotid == {1:}'.format(new_snapshot_id, snapshot))

            # And save the result
            new_snapshots.append(new_snapshot_id)

        # Reverse the short so it goes max->min
        sorted_snapshots = sorted(new_snapshots, reverse=True)

        if len(new_snapshots):
            self.dbinstance.commit()

        return sorted_snapshots[0]

    def GetSnapshots(self, backupconfigurationids=None, states=None):
        """
        Returns the list of existing snapshots

        :param backupconfigurationids: list of backup configuration ids to return snapshots for
        :param states: list of backup states to return snapshots for
        """
        conn = self.dbinstance.cursor()

        snapshots = []

        for result in conn.execute('SELECT snapshotid, startdate, state, cleanupindex, backupconfigurationid FROM snapshots'):
            snapshot = {
                'snapshotid': int(result[0]),
                'startdate': result[1],
                'state': int(result[2]),
                'cleanupindex': int(result[3]) if result[3] else '',
                'backupconfigurationid': int(result[4])
            }

            # Skip any backup configurations that are not desired by the caller
            if backupconfigurationids is not None:
                if str(snapshot['backupconfigurationid']) not in backupconfigurationids:
                    continue

            # Skip any states that are not desired by the caller
            if states is not None:
                if str(snapshot['state']) not in states:
                    continue

            snapshots.append(snapshot)

        return snapshots

    def Vacuum(self):
        """
        Shrink the database file to minimum size
        """
        conn = self.dbinstance.cursor()
        conn.execute('VACUUM')
        self.dbinstance.commit()

        # If we make it here
        return True

    def Rename(self, new_filename):
        """
        Rename the working database file to the specified file name
        """
        self.__close_db()
        os.rename(self.dbfile, new_filename)
        self.dbfile = new_filename
        self.__open_db()

        return True

    def BloatDatabase(self, table_suffix=None, granularity=1024 * 1024, minimum_compressed_size=5.1 * 1024 * 1024 * 1024):
        """
        Insert a table with random data in its columns to grow the database sufficiently to create a compressed database >5GB.
        File size typically needs to be in the 12GB+ range
        """
        def __bloat_db_find_test_compressed_size():
            import tempfile
            import gzip

            database_is_opened = False

            self.log.debug('Ensuring database closed in order to reliably generate a compressed file for testing')
            # Iff the database was opened then
            # Clean up and close the database for a reliable number
            if self.__is_db_opened():
                self.log.debug('Found the database open.')
                self.Vacuum()
                self.__close_db()
                database_is_opened = True

            # Generate a temp file for copying the compressed database to
            temp_file_info = tempfile.mkstemp()
            bloat_db_temp_file = temp_file_info[1]

            print('Compressing file for size check')
            # Apparently there is a bug in gzip.py that prevents the following from working:
            #
            # Compress the database to the new file
            with gzip.open(bloat_db_temp_file, 'wb') as gzip_file:
                with open(self.dbfile, 'rb') as input_file:
                    check_compressed_file_continue_loop = True
                    while check_compressed_file_continue_loop:
                        file_chunk = input_file.read(1024)
                        if len(file_chunk) == 0:
                            check_compressed_file_continue_loop = False
                        else:
                            gzip_file.write(file_chunk)

            # Get the compressed file size
            gzip_file_size = os.path.getsize(bloat_db_temp_file)

            file_sizes = (gzip_file_size, gzip_file_size / 1024, gzip_file_size / (1024 * 1024), gzip_file_size / (1024 * 1024 * 1024))

            print('\tSize: {0:} bytes, {1:} kilobytes, {2:} megabytes, {3:} gigabytes'.format(file_sizes[0], file_sizes[1], file_sizes[2], file_sizes[3]))

            # Remove the file since we don't really need it
            os.remove(bloat_db_temp_file)

            # And re-open the database iff it was previously opened
            if database_is_opened is True:
                self.log.debug('Database was found open. Re-opening.')
                self.__open_db()
                assert self.__is_db_opened()

            # return the size of the file
            return gzip_file_size

        original_compressed_size = __bloat_db_find_test_compressed_size()

        # in case the file doesn't get changed...
        new_compressed_size = original_compressed_size

        # Minimum 5.1 GB = 5.1*1024 MB = 5.1*1024*1024 KB = 5.1*1024*1024*1024 bytes
        if original_compressed_size < minimum_compressed_size:

            # Ensure the database is opened for use
            if self.__is_db_opened() is False:
                self.log.debug('Database was closed. Opening.')
                self.__open_db()
                assert self.__is_db_opened()

            # Determine the table name that will be used
            table_name = None
            if table_suffix is None:
                table_name = 'bloat_table'
            else:
                table_name = 'bloat_table_{0:}'.format(table_suffix)

            conn = self.dbinstance.cursor()

            # Ensure the table already exists
            conn.execute('CREATE TABLE IF NOT EXISTS {0:} ( a INTEGER PRIMARY KEY ASC, b DATETIME NOT NULL, c TEXT NOT NULL)'.format(table_name))

            # Loop on the file size being large enough
            #   Note: This will incur a bit of disk thrashing but it's the only reliable way to get the database size large enough
            while new_compressed_size <= minimum_compressed_size:

                # make sure we have a good cursor
                loop_conn = self.dbinstance.cursor()

                # Insert a lot of records to get the size up
                jumbo_count = 0
                while jumbo_count < granularity:
                    loop_conn.execute('INSERT INTO {0:} (a, b, c) VALUES(NULL, DATETIME(\'now\'), HEX(RANDOMBLOB(128)))'.format(table_name))
                    jumbo_count = jumbo_count + 1

                # Ensure the data is persistent
                self.dbinstance.commit()

                # Get the new size
                new_compressed_size = __bloat_db_find_test_compressed_size()

        # else don't do anything - the file's big enough

        return (original_compressed_size, new_compressed_size)
