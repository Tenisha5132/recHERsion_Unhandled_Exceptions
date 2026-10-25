SECURITY_HEADERS = {
    b'x-content-type-options': b'nosniff',
    b'x-frame-options': b'DENY',
    b'referrer-policy': b'strict-origin-when-cross-origin',
    b'permissions-policy': b'geolocation=(self), camera=(), microphone=()',
    b'cross-origin-opener-policy': b'same-origin',
    b'cross-origin-resource-policy': b'same-origin',
    b'x-permitted-cross-domain-policies': b'none',
    b'x-robots-tag': b'noindex, nofollow',
    b'content-security-policy': (
        b"default-src 'self'; base-uri 'self'; object-src 'none'; "
        b"frame-ancestors 'none'; form-action 'self'; "
        b"img-src 'self' data:; media-src 'self' blob:; "
        b"style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
        b"connect-src 'self'"
    ),
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


class NoStoreMiddleware:
    CACHEABLE_PREFIXES = ('/static/', '/media/sounds/')

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get('type') != 'http':
            await self.app(scope, receive, send)
            return

        path = scope.get('path') or ''
        cacheable = path.startswith(self.CACHEABLE_PREFIXES)

        async def send_with_cache_headers(message):
            if message.get('type') == 'http.response.start' and not cacheable:
                headers = list(message.get('headers') or [])
                present = {key.lower() for key, _ in headers}
                if b'cache-control' not in present:
                    headers.append((b'cache-control', b'no-store'))
                message = dict(message)
                message['headers'] = headers
            await send(message)

        await self.app(scope, receive, send_with_cache_headers)
