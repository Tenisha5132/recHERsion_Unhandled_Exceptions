import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as app_module
from fastapi.responses import JSONResponse


class TestCookieHardening(unittest.TestCase):
    def test_anonymous_cookie_is_httponly_and_lax(self):
        response = JSONResponse({'ok': True})
        with mock.patch.object(app_module, 'COOKIE_SECURE', False):
            app_module._set_anon_cookie(response, 'anon-123')
        cookie = response.headers['set-cookie'].lower()
        self.assertIn('rechers_anon_id=anon-123', cookie)
        self.assertIn('httponly', cookie)
        self.assertIn('samesite=lax', cookie)
        self.assertIn('max-age=2592000', cookie)
        self.assertNotIn('secure', cookie)

    def test_anonymous_cookie_is_secure_over_https(self):
        response = JSONResponse({'ok': True})
        with mock.patch.object(app_module, 'COOKIE_SECURE', True):
            app_module._set_anon_cookie(response, 'anon-123')
        self.assertIn('secure', response.headers['set-cookie'].lower())

    def test_cookie_secure_parser_accepts_common_values(self):
        from config import env_bool
        import os
        with mock.patch.dict(os.environ, {'TEST_BOOL': 'yes'}):
            self.assertTrue(env_bool('TEST_BOOL'))
        with mock.patch.dict(os.environ, {'TEST_BOOL': '0'}):
            self.assertFalse(env_bool('TEST_BOOL'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
