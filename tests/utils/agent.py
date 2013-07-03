"""Used for parsing agent metadata on the local machine."""
import base64
import json
import os


def _path():
    expander = os.path.expandvars
    joiner = os.path.join
    base = ('/etc/driveclient' if os.name != 'nt' else
            joiner(expander('%programdata%'), 'driveclient'))
    return joiner(base, 'bootstrap.json')


def _get_conf():
    path = _path()
    agent_conf = None
    with open(path, 'rt') as f:
        agent_conf = json.load(f)
    return agent_conf


class Agent(object):
    def __init__(self):
        conf = _get_conf()
        self._id = conf['AgentId']
        self._tenant = conf['AccountId']
        self._user = conf['Username']
        self._key = base64.b64decode(conf['AgentKey'])
        self._registered = conf['IsRegistered']

    @property
    def id(self):
        return self._id

    @property
    def tenant(self):
        return self._tenant

    @property
    def user(self):
        return self._user

    @property
    def key(self):
        return self._key

    @property
    def registered(self):
        return self._registered
