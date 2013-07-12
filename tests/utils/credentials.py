import json
import os


def _parse_config():
    path = os.path.join(os.path.expanduser('~'),
                        '.pysdk', 'credentials.json')
    data = None
    try:
        with open(path) as f:
            data = json.load(f)
    except IOError:
        form = 'Did you remember to install {0}?'
        raise RuntimeError(form.format(path))

    return (data.get('username', None),
            data.get('apikey', None),
            data.get('email', None),
            data.get('tenant', None))


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
