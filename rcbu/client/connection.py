from rcbu.common import auth
from rcbu.common import exceptions
from rcbu.common import http

from dateutil import parser
import requests
import six


def _normalize_endpoint(url):
    idx = url.rfind('/')
    return url[:idx]


def _find_endpoint(target, region):
    region_matcher = lambda x: x['region'].upper() == region.upper()
    try:
        return next(six.moves.filter(region_matcher,
                                     target['endpoints']))
    except StopIteration:
        return None


def _find_backup_endpoint(catalogue, region):
    backup_matcher = lambda x: x['type'] == u'rax:backup'
    target = next(six.moves.filter(backup_matcher, catalogue))

    # NOTE(cabrera): attempt to grab a region-specific endpoint. If
    # this fails, then either the region provided was not valid or
    # there are no region-specific endpoints for this tenant.
    endpoint = _find_endpoint(target, region)

    # NOTE(cabrera): if no endpoint was detected for a specific region
    # or no region was provided, attempt to grab a generic endpoint
    if not endpoint:
        return None

    return _normalize_endpoint(endpoint[u'publicURL'])


class Connection(object):
    def __init__(self, username, region, apikey=None, password=None):
        assert apikey or password

        resp = None
        # If apikey and password are given, give priority to
        # authentication via API key.
        if apikey:
            resp = auth.authenticate(username, apikey=apikey)
        else:
            resp = auth.authenticate(username, password=password)

        self._token = resp['access']['token']['id']
        endpoints = resp['access']['serviceCatalog']

        self._endpoint = _find_backup_endpoint(endpoints, region)
        if not self._endpoint:
            raise exceptions.NoEndpointFound(username, region)

        self._username = username
        self._tenant = resp['access']['token']['tenant']['id']
        self._expiry = resp['access']['token']['expires']
        self._session = requests

    def __repr__(self):
        msg = ('<Connection host:{0} tenant:{1} username:{2} expires:{3}>')
        return msg.format(self.host, self.tenant,
                          self.username,
                          self.expires.isoformat())

    @property
    def token(self):
        return self._token

    @property
    def tenant(self):
        return self._tenant

    @property
    def username(self):
        return self._username

    @property
    def host(self):
        return self._endpoint

    @property
    def api_version(self):
        return self.host.split('/')[-1].lstrip('v')

    @property
    def api_version_tuple(self):
        return tuple(int(i) for i in self.api_version.split('.'))

    @property
    def expires(self):
        date = parser.parse(self._expiry)
        return date

    def request(self, method, url, headers=None, data=None, verify=True):
        '''Method is an http.Http enum, such as http.Http.get.'''
        # todo: add reauth when token is nearing expiration here
        headers_ = {
            'x-auth-token': self.token,
            'content-type': 'application/json',
            'user-agent': 'python-cloudbackup-sdk'
        }
        if headers:
            headers_.update(headers)
        call = getattr(self._session, http.enum_to_method(method))
        resp = call(url, headers=headers_, data=data, verify=verify)
        resp.raise_for_status()
        return resp
