import json

import requests

from rcbu.common.constants import IDENTITY_TOKEN_URL


def authenticate(apikey=None, password=None, *, username):
    if apikey:
        return _auth(username=username, apikey=apikey)

    if password:
        return _auth(username=username, password=password)


def get_token(apikey=None, password=None, *, username):
    r = authenticate(username=username, apikey=apikey, password=password)
    return r['access']['token']['id']


def _auth(apikey=None, password=None, *, username):
    creds = {'username': username}
    assert password or apikey

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
