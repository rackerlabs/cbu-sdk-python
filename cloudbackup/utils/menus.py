"""
Menu Printing and select
"""
from __future__ import print_function

import logging


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
        printMenu(menu)
        try:
            selection = int(raw_input('{0:}: '.format(prompt)))
            return getMenuEntry(menu, selection)

        except Exception as ex:
            print('Invalid selection')
            log.debug('Prompt Selection - Exception: {0:}'.format(ex))


def promptSimple(menu, prompt, prefix=''):
    return promptSelection(menu, prompt)['text']


def promptYesNoCancel(prompt, prefix=''):
    """
    Simple Yes/No/Cancel prompt
    """
    menu = [
        {'index': 1, 'text': 'Yes', 'type': 'YES'},
        {'index': 2, 'text': 'No', 'type': 'NO'},
        {'index': 3, 'text': 'Cancel', 'type': 'EXIT'}
    ]
    return promptSimple(menu, prompt)
