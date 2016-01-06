"""
TimeZone Utility
"""
from __future__ import print_function

import logging

import pytz
import tzlocal
import tzlocal.windows_tz


def get_timezone(WindowsZoneName=True):
    """
    Get the TimeZone Name

    if WindowsZoneName is True, then it returns the name used by the Microsoft Windows Platform
    otherwise it returns the Olsen name (used by all other platforms)

    Note: this needs to get tested on Windows
    """
    log = logging.getLogger(__name__)
    localzone = tzlocal.get_localzone()
    if localzone is None:
        log.error('tzlocal did not provide a time zone configuration')
        raise pytz.UnknownTimeZoneError('Cannot find  any time zone configuration')
    else:
        olsen_name = localzone.zone
        if WindowsZoneName:
            try:
                windows_name = tzlocal.windows_tz.tz_win[olsen_name]
                log.info('Mappped Olsen Time Zone Name (' + olsen_name + ') to Windows Time Zone Name (' + windows_name + ')')
                return windows_name
            except LookupError:
                log.error('Unable to map Olsen Time Zone Name (' + olsen_name + ') to Windows Time Zone Name')
                return 'Unknown'
        else:
            return olsen_name

def get_v1_timezone_name_list():
    # Return the Microsoft Windows Time Zone Names
    return sorted(tzlocal.windows_tz.win_tz.keys())


def get_v2_timezone_name_list():
    # Return the Olsen Time Zone Names
    return sorted(tzlocal.windows_tz.tz_win.keys())
