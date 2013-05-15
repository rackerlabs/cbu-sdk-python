import unittest

from httpretty import HTTPretty, httprettified

import rcbu.common.auth as auth


def _prepare_mock_post(status, body=None):
    HTTPretty.register_uri(HTTPretty.POST, '_',
                           status=status, body=body)


class TestAuth(unittest.TestCase):

    @httprettified
    def test_auth_by_password_raises_if_invalid_creds(self):
        _prepare_mock_post(status=403)
        self.assertRaises(Exception,
                          auth.authenticate(password='bad', username='b'))

    @httprettified
    def test_auth_by_apikey_raises_if_invalid_creds(self):
        _prepare_mock_post(status=403)
        self.assertRaises(Exception,
                          auth.authenticate(apikey='bad', username='b'))

    @httprettified
    def test_auth_returns_catalog_on_success(self):
        _prepare_mock_post(status=200, body='yay')
        catalog = auth.authenticate(username='b', password='good')
        self.assertEqual(catalog, 'yay')

    @httprettified
    def test_get_token_by_password_raises_if_invalid_creds(self):
        _prepare_mock_post(status=403)
        self.assertRaises(Exception,
                          auth.get_token(password='bad', username='b'))

    @httprettified
    def test_get_token_by_apikey_raises_if_invalid_creds(self):
        _prepare_mock_post(status=403)
        self.assertRaises(Exception,
                          auth.get_token(apikey='bad', username='b'))

    @httprettified
    def test_get_token_returns_token_on_success(self):
        _prepare_mock_post(status=200, body='token')
        token = auth.get_token(username='b', password='good')
        self.assertEqual(token, 'token')
