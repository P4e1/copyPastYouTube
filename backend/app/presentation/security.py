"""Заголовки ответа и лимит попыток регистрации и входа."""

import time

from starlette.responses import JSONResponse

from app.domain.security import SlidingWindow

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}
AUTH_PATHS = {"/auth/login", "/auth/register"}


class SecurityHeadersMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers") or [])
                existing = {name.lower() for name, _ in headers}
                for name, value in SECURITY_HEADERS.items():
                    encoded = name.lower().encode()
                    if encoded not in existing:
                        headers.append((encoded, value.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)


class AuthRateLimitMiddleware:
    def __init__(self, app, limit: int = 20) -> None:
        self.app = app
        self.limit = limit
        self.window = SlidingWindow()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("method") == "POST" and scope.get("path") in AUTH_PATHS:
            client = scope.get("client")
            ip = client[0] if client else "unknown"
            if not self.window.allow(ip, limit=self.limit, window=60, now=time.monotonic()):
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Слишком много попыток входа. Подождите минуту."},
                    headers={"Retry-After": "60"},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
