import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security import NoStoreMiddleware, SECURITY_HEADERS, SecurityHeadersMiddleware


async def _run(messages):
    async def inner(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
        await send({'type': 'http.response.body', 'body': b'ok'})

    sent = []

    async def send(message):
        sent.append(message)

    await SecurityHeadersMiddleware(inner)({'type': 'http'}, None, send)
    return sent


class TestSecurityHeaders(unittest.TestCase):
    def test_headers_are_added_to_http_responses(self):
        sent = asyncio.run(_run([]))
        headers = dict(sent[0]['headers'])
        for key, value in SECURITY_HEADERS.items():
            self.assertEqual(headers[key], value)
        self.assertEqual(headers[b'content-type'], b'text/plain')
        csp = headers[b'content-security-policy'].decode('ascii')
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("media-src 'self' blob:", csp)

    def test_headers_do_not_duplicate_existing_values(self):
        async def inner(scope, receive, send):
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [(b'x-frame-options', b'SAMEORIGIN')],
            })

        sent = []

        async def send(message):
            sent.append(message)

        asyncio.run(SecurityHeadersMiddleware(inner)({'type': 'http'}, None, send))
        values = [value for key, value in sent[0]['headers'] if key == b'x-frame-options']
        self.assertEqual(values, [b'SAMEORIGIN'])


async def _cache_headers(path):
    async def inner(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})

    sent = []

    async def send(message):
        sent.append(message)

    await NoStoreMiddleware(inner)({'type': 'http', 'path': path}, None, send)
    return dict(sent[0]['headers'])


class TestNoStoreMiddleware(unittest.TestCase):
    def test_dynamic_pages_are_not_cached(self):
        for path in ['/', '/timeline', '/privacy', '/api/chat', '/healthz']:
            headers = asyncio.run(_cache_headers(path))
            self.assertEqual(headers[b'cache-control'], b'no-store', path)

    def test_static_assets_keep_their_cache_policy(self):
        for path in ['/static/site.css', '/media/sounds/rain.wav']:
            headers = asyncio.run(_cache_headers(path))
            self.assertNotIn(b'cache-control', headers, path)

    def test_existing_cache_header_is_not_overwritten(self):
        async def inner(scope, receive, send):
            await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'cache-control', b'public, max-age=60')]})

        sent = []

        async def send(message):
            sent.append(message)

        asyncio.run(NoStoreMiddleware(inner)({'type': 'http', 'path': '/api/chat'}, None, send))
        values = [value for key, value in sent[0]['headers'] if key == b'cache-control']
        self.assertEqual(values, [b'public, max-age=60'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
