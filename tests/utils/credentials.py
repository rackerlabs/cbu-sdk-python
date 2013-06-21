from __future__ import print_function
import configparser
import os
import sys


def _parse_config():
    path = os.path.join(os.path.expanduser('~'),
                        '.pysdk', 'credentials.conf')
    config = configparser.ConfigParser()
    try:
        config.read(path)
    except configparser.ParsingError as e:
        form = 'Did you remember to install/fill in {0}?'
        print(form.format(path), file=sys.stderr)

    creds = config['credentials']
    return (creds.get('username', None),
            creds.get('apikey', None),
            creds.get('email', None),
            creds.get('tenant', None))


class Credentials(object):
    def __init__(self):
        name, key, email, tenant = _parse_config()
        self._name = name
        self._key = key
        self._email = email
        self._tenant = tenant

    @property
    def name(self):
        return self._name

    @property
    def key(self):
        return self._key

    @property
    def email(self):
        return self._email

    @property
    def tenant(self):
        return self._tenant
