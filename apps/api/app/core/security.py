import logging
from time import perf_counter
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi.responses import JSONResponse
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import reset_request_id, set_request_id

_logger = logging.getLogger("app.http")

_SECURITY_HEADERS: dict[str, str] = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


def _route_template(scope: Scope) -> str:
    route: Any = scope.get("route")
    route_path = getattr(route, "path", None)
    return route_path if isinstance(route_path, str) else "unmatched"


def _request_host(scope: Scope) -> str | None:
    raw_host = Headers(scope=scope).get("host")
    if raw_host is None:
        return None

    try:
        parsed = urlsplit(f"//{raw_host}")
        _ = parsed.port
    except ValueError:
        return None

    if (
        parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        return None

    return parsed.hostname.lower()


class RequestSecurityMiddleware:
    """Adds safe request context, response headers, access logs, and fail-closed errors."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        environment: str,
        trusted_hosts: tuple[str, ...],
    ) -> None:
        self.app = app
        self.environment = environment
        self.trusted_hosts = frozenset(host.lower() for host in trusted_hosts)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        context_token = set_request_id(request_id)
        started_at = perf_counter()
        status_code = 500
        response_started = False

        async def send_with_security_headers(message: Message) -> None:
            nonlocal response_started, status_code

            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                headers = MutableHeaders(scope=message)

                for name, value in _SECURITY_HEADERS.items():
                    headers[name] = value

                headers["X-Request-ID"] = request_id
                if "Cache-Control" not in headers:
                    headers["Cache-Control"] = "no-store"

                if self.environment == "production" and scope.get("scheme") == "https":
                    headers["Strict-Transport-Security"] = "max-age=31536000"

            await send(message)

        try:
            if _request_host(scope) not in self.trusted_hosts:
                response = JSONResponse(
                    status_code=400,
                    content={"error": "invalid_host", "request_id": request_id},
                )
                await response(scope, receive, send_with_security_headers)
            else:
                await self.app(scope, receive, send_with_security_headers)
        except Exception as exception:
            _logger.error(
                "unhandled_exception",
                extra={
                    "request_id": request_id,
                    "exception_type": type(exception).__name__,
                },
            )

            if response_started:
                raise

            response = JSONResponse(
                status_code=500,
                content={"error": "internal_error", "request_id": request_id},
            )
            await response(scope, receive, send_with_security_headers)
        finally:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            _logger.info(
                "http_request",
                extra={
                    "request_id": request_id,
                    "method": scope.get("method", "UNKNOWN"),
                    "route": _route_template(scope),
                    "status": status_code,
                    "duration_ms": duration_ms,
                },
            )
            reset_request_id(context_token)
