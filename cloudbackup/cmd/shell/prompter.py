from __future__ import print_function

import cloudbackup.utils.menus
from cloudbackup.utils import tz


def doPromptBackupConfigurationName(user_aborted=False):
    name = None
    if not user_aborted:
        name = cloudbackup.utils.menus.promptUserInputString(
            'Backup Configuration Name',
            '',
        )
    return name

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

    def promptTimeZone():
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

    def promptStartTime():
        data['StartTime']['hour'] = cloudbackup.utils.menus.promptUserInputNumber(
            'Hour (24-hour format)',
            '',
            -1,
            24,
            show_range=True
        )
        if data['StartTime']['hour'] is None:
            print('Aborting')
            user_aborted = True

        else:
            data['StartTime']['minute'] = cloudbackup.utils.menus.promptUserInputNumber(
                'Minute',
                '',
                -1,
                60,
                show_range=True
            )
            if data['StartTime']['minute'] is None:
                print('Aborting')
                user_aborted = True

            else:
                if data['StartTime']['hour'] > 12:
                    data['StartTime']['amOrPm'] = 'PM'
                else:
                    data['StartTime']['amOrPm'] = 'AM'

                promptTimeZone()


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
                promptTimeZone()

        else:
            # TODO: Prompt for how often to run non-hourly intervals
            data['interval'] = 1

    if not user_aborted:
        return data
    else:
        return None


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
