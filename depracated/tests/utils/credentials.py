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
            data.get('tenant', None),
            data.get('region', None))


class Credentials(object):
    def __init__(self):
        name, key, email, tenant, region = _parse_config()
        self.name = name
        self.key = key
        self.email = email
        self.tenant = tenant
        self.region = region
