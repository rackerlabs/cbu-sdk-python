import json

import requests

from rcbu.common.constants import IDENTITY_TOKEN_URL


def authenticate(username, apikey=None, password=None):
    assert password or apikey
    if apikey:
        return _auth(username=username, apikey=apikey)

    else:
        return _auth(username=username, password=password)


def get_token(username, apikey=None, password=None):
    r = authenticate(username=username, apikey=apikey, password=password)
    return r['access']['token']['id']


def _auth(username, apikey=None, password=None):
    creds = {'username': username}

    auth_type = None
    if password:
        creds['password'] = password
        auth_type = {'passwordCredentials': creds}
    else:
        creds['apiKey'] = apikey
        auth_type = {'RAX-KSKEY:apiKeyCredentials': creds}

    wrapper = {'auth': auth_type}
    data = json.dumps(wrapper)
    r = requests.post(IDENTITY_TOKEN_URL, data=data,
                      headers={'content-type': 'application/json'})
    if not r.ok:
        r.raise_for_status()
    return r.json()
