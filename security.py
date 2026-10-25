SECURITY_HEADERS = {
    b'x-content-type-options': b'nosniff',
    b'x-frame-options': b'DENY',
    b'referrer-policy': b'strict-origin-when-cross-origin',
    b'permissions-policy': b'geolocation=(self), camera=(), microphone=()',
    b'cross-origin-opener-policy': b'same-origin',
}


class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get('type') != 'http':
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message.get('type') == 'http.response.start':
                headers = list(message.get('headers') or [])
                present = {key.lower() for key, _ in headers}
                for key, value in SECURITY_HEADERS.items():
                    if key not in present:
                        headers.append((key, value))
                message = dict(message)
                message['headers'] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
