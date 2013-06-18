import unittest

from httpretty import HTTPretty, httprettified
from requests.exceptions import HTTPError

import rcbu.common.auth as auth
from rcbu.common.constants import IDENTITY_TOKEN_URL


def _prepare_mock_post(status, body=''):
    HTTPretty.register_uri(HTTPretty.POST, IDENTITY_TOKEN_URL,
                           status=status, body=body)


class TestAuth(unittest.TestCase):

    @httprettified
    def test_auth_by_password_raises_if_invalid_creds(self):
        _prepare_mock_post(status=403)
        with self.assertRaises(HTTPError):
            auth.authenticate(password='bad', username='b')

    @httprettified
    def test_auth_by_apikey_raises_if_invalid_creds(self):
        _prepare_mock_post(status=403)
        with self.assertRaises(HTTPError):
            auth.authenticate(apikey='bad', username='b')

    @httprettified
    def test_auth_raises_if_neither_apikey_or_password_provided(self):
        _prepare_mock_post(status=200)
        with self.assertRaises(AssertionError):
            auth.authenticate(username='b')

    @httprettified
    def test_auth_returns_catalog_on_success(self):
        _prepare_mock_post(status=200, body='{"yay": 1}')
        catalog = auth.authenticate(username='b', password='good')
        self.assertEqual(catalog, {'yay': 1})

    @httprettified
    def test_get_token_by_password_raises_if_invalid_creds(self):
        _prepare_mock_post(status=403)
        with self.assertRaises(HTTPError):
            auth.get_token(password='bad', username='b')

    @httprettified
    def test_get_token_by_apikey_raises_if_invalid_creds(self):
        _prepare_mock_post(status=403)
        with self.assertRaises(HTTPError):
            auth.get_token(apikey='bad', username='b')

    @httprettified
    def test_get_token_returns_token_on_success(self):
        _prepare_mock_post(status=200,
                           body='{"access": {"token": {"id": "token"}}}')
        token = auth.get_token(username='b', password='good')
        self.assertEqual(token, 'token')
