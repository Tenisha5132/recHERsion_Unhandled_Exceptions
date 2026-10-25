import re
import uuid

REQUEST_ID_HEADER = b'x-request-id'
REQUEST_ID_PATTERN = re.compile(r'^[A-Za-z0-9._-]{1,64}$')


def request_id_from_scope(scope):
    headers = dict(scope.get('headers') or [])
    candidate = headers.get(REQUEST_ID_HEADER, b'').decode('latin-1').strip()
    if candidate and REQUEST_ID_PATTERN.match(candidate):
        return candidate
    return uuid.uuid4().hex


class RequestIdMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get('type') != 'http':
            await self.app(scope, receive, send)
            return

        request_id = request_id_from_scope(scope)

        async def send_with_request_id(message):
            if message.get('type') == 'http.response.start':
                headers = list(message.get('headers') or [])
                if not any(key.lower() == REQUEST_ID_HEADER for key, _ in headers):
                    headers.append((REQUEST_ID_HEADER, request_id.encode('ascii')))
                message = dict(message)
                message['headers'] = headers
            await send(message)

        await self.app(scope, receive, send_with_request_id)
