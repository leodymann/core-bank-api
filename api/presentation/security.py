import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request, Response, status
from starlette.types import ASGIApp, Receive, Scope, Send

from api.infra.config import get_settings


PUBLIC_PATH_PREFIXES = ("/health", "/docs", "/openapi.json", "/redoc")


async def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    settings = get_settings()

    if not settings.auth_enabled:
        return

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing API key",
        )


class InMemoryRateLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        settings = get_settings()

        if (
            not settings.rate_limit_enabled
            or request.url.path.startswith(PUBLIC_PATH_PREFIXES)
        ):
            await self.app(scope, receive, send)
            return

        client = request.headers.get("x-api-key")

        if client is None:
            client = request.client.host if request.client else "unknown"

        now = time.monotonic()
        window_start = now - settings.rate_limit_window_seconds
        hits = self._hits[client]

        while hits and hits[0] < window_start:
            hits.popleft()

        if len(hits) >= settings.rate_limit_requests:
            response = Response(
                content='{"detail":"rate limit exceeded"}',
                media_type="application/json",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": str(settings.rate_limit_window_seconds),
                },
            )

            await response(scope, receive, send)
            return

        hits.append(now)

        await self.app(scope, receive, send)