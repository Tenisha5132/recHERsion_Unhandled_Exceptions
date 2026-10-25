import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security import SECURITY_HEADERS, SecurityHeadersMiddleware


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


if __name__ == '__main__':
    unittest.main(verbosity=2)
