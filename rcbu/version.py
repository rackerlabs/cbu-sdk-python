import re


def parse_version():
    data = None
    with open('../README.rst', 'rt') as f:
        data = f.read()
    version_re = r':version: (\d)\.(\d)\.(\d)'
    return tuple([int(k) for k in re.search(version_re, data).groups()])


version_tuple = parse_version()
version = '.'.join(version_tuple)
