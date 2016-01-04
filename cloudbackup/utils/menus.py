"""
Menu Printing and select
"""
from __future__ import print_function

import logging
import re

import six


def printMenu(menu, showExit=True, prefix=''):
    for entry in menu:
        if (entry['type'] == 'EXIT' and showExit is True) or entry['type'] != 'EXIT':
            print('{0:}{1:02d}) {2:}'.format(prefix, entry['index'], entry['text']))


def getMenuEntry(menu, selection):
    for entry in menu:
        if entry['index'] == selection:
            return entry
    return None


def promptSelection(menu, prompt, prefix=''):
    log = logging.getLogger()

    user_terminated = False
    while not user_terminated:
        printMenu(menu, True, prefix)
        try:
            if six.PY2:
                selection = int(raw_input('{0:}: '.format(prompt)))
            else:
                selection = int(input('{0:}: '.format(prompt)))

            menu_entry = getMenuEntry(menu, selection)
            if menu_entry is not None:
                return menu_entry
            else:
                print('Invalid Selection. Try again.')

        except Exception as ex:
            print('Invalid selection')
            log.debug('Prompt Selection - Exception: {0:}'.format(ex))


def promptSimple(menu, prompt, prefix=''):
    return promptSelection(menu, prompt, prefix)['text']


def promptYesNoCancel(prompt, prefix=''):
    """
    Simple Yes/No/Cancel prompt
    """
    menu = [
        {'index': 1, 'text': 'Yes', 'type': 'YES'},
        {'index': 2, 'text': 'No', 'type': 'NO'},
        {'index': 3, 'text': 'Cancel', 'type': 'EXIT'}
    ]
    return promptSimple(menu, prompt, prefix)

def promptUserInputString(prompt, prefix='', min_length=0, max_length=99999):
    log = logging.getLogger()
    user_result = None

    while user_result is None:
        try:
            print('Press CTRL+C to cancel')
            if six.PY2:
                user_result = raw_input('{0}: '.format(prompt))

            else:
                user_result = input('{0}: '.format(prompt))

            if len(user_result) <= min_length:
                print('Value too short. {0} <= {1}. Please try again...'
                      .format(len(user_result), min_length))
                user_result = None

            elif len(user_result) >= max_length:
                print('Value too long. {0} >= {1}. Please try again...'
                      .format(len(user_result), max_length))
                user_result = None

        except KeyboardInterrupt:
            print('Aborting.')
            user_result = None
            break

        return user_result

def promptUserInputNumber(prompt, prefix='', min_value=0, max_value=99999, show_range=False):
    log = logging.getLogger()
    user_result = None

    while user_result is None:
        try:
            print('Press CTRL+C to cancel')
            if show_range:
                print('Acceptable Range: {0} <= X <= {1}'
                      .format(min_value, max_value))

            if six.PY2:
                user_result = raw_input('{0}: '.format(prompt))

            else:
                user_result = input('{0}: '.format(prompt))

            validator = re.compile('^\d*$')
            match_result = validator.match(user_result)

            if match_result:
                value = int(user_result)
                if value <= min_value:
                    print('Value is too small. {0} <= {1}. Please try again...'
                          .format(user_result, min_value))
                    user_result = None

                elif value >= max_value:
                    print('Value is too large. {0} >= {1}. Please try again...'
                          .format(user_result, max_value))
                    user_result = None

            else:
                print('Value is not a number. Please try again.')
                user_result = None

        except KeyboardInterrupt:
            print('Aborting.')
            user_result = None
            break

    if user_result is None:
        return None
    else:
        return int(user_result)
