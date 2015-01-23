"""
Print Utility

Wraps the built-in print such that the output is captured to a configurable file.
The file is specified in the [globals] section of the agenttests.ini:

[globals]
print=<file>

If not specified (print = None or '') then defaults to sys.stdout.
If the 'file' parameter to print() is something other than sys.stdout, then both
    the configured file and the specified file will receive the output.

The caller may optionally call setPrefix() to set prefix to all print statements.
If the prefix is None, then it will be skipped. There is no need to have a space
at the end of the prefix as one will automatically be added. This is useful to
record the output in a manner that will be re-orderable later on - for example,
prepend the test name and platform when splitting out platforms to multiple threads
to speed up processing.
"""
from __future__ import print_function

import os
import sys

try:
    # Python2
    import __builtin__ as builtins
except ImportError:
    # Python3
    import builtins

# Save the build in print function so we can use it
__actual_print = print
__name_prefix = dict()
__name_key_fn = os.getpid
__output_file = None


def setOutputFile(filename):
    global __output_file
    __output_file = filename


def getOutputFile():
    global __output_file
    return __output_file


def __local_print(*args, **kwargs):
    """
    Local print() implementation to enable directing to two sources - the programmed output (stdout or specified by 'file') and a configured
    output, specified via the configuration file; as well as adding a per-line prefix
    """
    global __name_prefix
    global __output_file

    # Capture the standard arguments
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    out = kwargs.get('file', sys.stdout)
    flush = kwargs.get('flush', False)
    sysout = out

    # Replace the output file
    filename = __output_file
    if not (filename is None):
        if len(filename):
            out = open(filename, 'a+')

    print_args = list(args)

    # Add the prefix
    key = __name_key_fn()
    if key in __name_prefix:
        print_args.insert(0, __name_prefix[key])

    # Append the terminator
    print_args.append(end)

    # Print everything out - note: we reset the terminator here so as to get everything on a single line as desired
    for arg in print_args:
        __actual_print(arg, sep=sep, end='', file=out)
        if sysout != sys.stdout:
            __actual_print(arg, sep=sep, end='', file=sysout)

    # Clear the pipeline if neeeded
    if flush:
        out.flush()
        sysout.flush()


def setPrefix(key, name=None):
    """
    Set the output prefix
    """
    global __name_prefix
    __name_prefix[key] = name


def getPrefix(key):
    """
    Retrieve the output prefix
    """
    global __name_prefix
    if key in __name_prefix:
        return __name_prefix[key]
    else:
        return None


def clearPrefix(key):
    """
    Clear output prefix
    """
    del __name_prefix[key]


def setKeyFn(fn):
    """
    set the prefix dictionary key function

    Note: This is not multithread/multiprocess safe. It should only be set before anything starts setting the keys.
    """
    global __name_key_fn
    __name_key_fn = fn


def getKeyFn():
    """
    return the prefix dictionary key function
    """
    return __name_key_fn

# Overwrite the builtin print our own copy
builtins.print = __local_print
