"""
Rackspace Cloud Backup API Utilities
"""
from __future__ import print_function
import cloudbackup.utils.printer  # noqa

import logging
import os


def announce_banner(banner):
    """
    Output a banner to both the log and normal output functionality
    """
    log = logging.getLogger(__name__)
    marker = '===================================================='
    log.info(marker)
    log.info(banner)
    log.info(marker)

    print(marker)
    print(banner)


def normpath(platfrm, fpath):
    """
    Normalize the path in an expected manner
    """
    if platfrm.find('windows') > -1:
        return fpath.replace('/', '\\')
    else:
        return fpath.replace('\\', '/')


def joinpath(platfrm, dirname, *base):
    ''' Join paths and normalize it based on the platform
    '''
    return normpath(platfrm, os.path.join(dirname, *base))


def basename(platfrm, fpath):
    """
    Return the basename of the path given
    """
    if platfrm.find('windows') > - 1:
        return os.path.basename(normpath('linux', fpath))
    else:
        return os.path.basename(fpath)


def splitall(platfrm, fpath):
    ''' return a list with the path broken up'''
    if platfrm.find('windows') > -1:
        np = normpath('linux', fpath)
    else:
        np = fpath[:]
    plist = list()
    while True:
        sp = os.path.split(np)
        if len(sp[0]) == 0:
            # the case for Windows
            plist.append(sp[1])
            break
        elif len(sp[1]) == 0:
            # the case for Posix
            plist.append(sp[0])
            break
        else:
            plist.append(sp[1])
            np = sp[0]
    plist.reverse()
    return plist
