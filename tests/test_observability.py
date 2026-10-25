import asyncio
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from observability import RequestIdMiddleware, request_id_from_scope


async def _response_headers(scope):
    async def inner(inner_scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})

    sent = []

    async def send(message):
        sent.append(message)

    await RequestIdMiddleware(inner)(scope, None, send)
    return dict(sent[0]['headers'])


class TestRequestIdMiddleware(unittest.TestCase):
    def test_generates_a_request_id(self):
        scope = {'type': 'http', 'headers': []}
        headers = asyncio.run(_response_headers(scope))
        value = headers[b'x-request-id'].decode('ascii')
        self.assertTrue(re.fullmatch(r'[0-9a-f]{32}', value))

    def test_preserves_safe_request_id(self):
        scope = {'type': 'http', 'headers': [(b'x-request-id', b'req-123.test')]}
        self.assertEqual(request_id_from_scope(scope), 'req-123.test')
        headers = asyncio.run(_response_headers(scope))
        self.assertEqual(headers[b'x-request-id'], b'req-123.test')

    def test_rejects_unsafe_request_id(self):
        scope = {'type': 'http', 'headers': [(b'x-request-id', b'bad value\ninjected')]}
        value = request_id_from_scope(scope)
        self.assertNotIn('\n', value)
        self.assertTrue(re.fullmatch(r'[0-9a-f]{32}', value))


if __name__ == '__main__':
    unittest.main(verbosity=2)
