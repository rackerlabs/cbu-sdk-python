"""
Menu Printing and select
"""
from __future__ import print_function

import logging
import re

import six


def printMenu(menu, showExit=True, prefix=''):
    """Prints the menu for the user to see

    :param menu: an array of menu entries, each menu entry is a dictionary
    :param showExit: boolean for whether or not to show the EXIT entry
    :param prefix: string to print in from of the menu entry (e.g for formatting)

    :returns: n/a

    The 'menu' parameter is an array of dictionary values. Each entry in the array
    translates to a single menu item that looks like the following dictionary:
        {
            'type': '<type>',
            'index': #<index>#,
            'text': '<text>'
        }

    The dictionary may contain other entries. The 'type' and 'text' fields are both
    string values. The 'type' value only has one special value ('EXIT') used to denote
    the Exit menu entry; it may otherwise be any arbitrary string. The 'index' field
    is typically an integer used to provide the value input for the user to select
    the menu item with.

    There are two easy ways to create the menu dictionary:

        menu = [
            {'type': 'entry', 'index': 0, 'text': 'First Entry'},
            {'type': 'entry', 'index': 1, 'text': 'Second Entry'},
            {'type': 'entry', 'index': 2, 'text': 'Third Entry'},
        ]

    or 

        menu = []
        for x in range(3):
            menu.append({
                'type': 'entry',
                'index': len(menu),
                'text': 'Entry #{0}'.format(x)
            })
    """
    for entry in menu:
        if (entry['type'] == 'EXIT' and showExit is True) or entry['type'] != 'EXIT':
            print('{0:}{1:02d}) {2:}'.format(prefix, entry['index'], entry['text']))


def getMenuEntry(menu, selected_index):
    """Given a menu and a selected index, return the full menu entry

    :param menu: array of menu entries, see printMenu() for details
    :param selected_index: integer, selected index value 
    :returns: dictionary, menu entry
    """
    for entry in menu:
        if entry['index'] == selected_index:
            return entry
    return None


def promptSelection(menu, prompt, prefix=''):
    """Prompt the user using the provided menu to determine a selection

    :param menu: array of menu entries, see printMenu() for details
    :param prompt: string, message to the user for selecting a menu entry
    :param prefix: string, text to print before the menu entry to format the display
    :returns: dictionary, menu entry
    """
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
    """Simple wrapper around promptSelection() to get the selected menu text

    :param menu: array of menu entries, see printMenu() for details
    :param prompt: string, message to the user for selecting a menu entry
    :param prefix: string, text to print before the menu entry to format the display
    :returns: string, menu entry text
    """
    return promptSelection(menu, prompt, prefix)['text']


def promptYesNoCancel(prompt, prefix=''):
    """Simple Yes/No/Cancel prompt

    :param prompt: string, message to the user for selecting a menu entry
    :param prefix: string, text to print before the menu entry to format the display
    :returns: string, menu entry text
    """
    menu = [
        {'index': 1, 'text': 'Yes', 'type': 'YES'},
        {'index': 2, 'text': 'No', 'type': 'NO'},
        {'index': 3, 'text': 'Cancel', 'type': 'EXIT'}
    ]
    return promptSimple(menu, prompt, prefix)

def promptUserInputString(prompt, prefix='', min_length=0, max_length=99999):
    """Prompt the user for an arbitrary string

    :param prompt: string, message to user about what to enter
    :param prefix: string, text to print before the prompt for formatting
    :param min_length: integer, minimum length of the string to accept (min_length, x]
    :param max_length: integer, maximum length of the string to accept [x, max_length)
    :returns: string, text from user or None if user cancels

    Note: User is directed to press CTRL+C to cancel the entry
    """
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
    """Prompt the user for an arbitrary integer value

    :param prompt: string, message to user about what to enter
    :param prefix: string, text to print before the prompt for formatting
    :param min_value: integer, minimum value of the string to accept (min_value, x]
    :param max_value: integer, maximum value of the string to accept [x, max_value)
    :param show_range: boolean, whether or not to show the valid range of acceptable values
    :returns: integer, integer from user or None if user cancels

    Note: User is directed to press CTRL+C to cancel the entry
    """
    log = logging.getLogger()
    user_result = None

    validator = re.compile('^\d*$')
    while user_result is None:
        try:
            print('Press CTRL+C to cancel')
            if show_range:
                print('Acceptable Range: {0} < X < {1}'
                      .format(min_value, max_value))

            if six.PY2:
                user_result = raw_input('{0}: '.format(prompt))

            else:
                user_result = input('{0}: '.format(prompt))

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


def promptUserAnyKey(prompt='Press any key to continue'):
    """Prompt user to press any key as a delay or paging method"
    """
    if six.PY2:
        raw_input(prompt)
    else:
        input(prompt)
