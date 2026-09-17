from collections.abc import Mapping

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_request_id

_HTTP_ERROR_CODES: Mapping[int, str] = {
    400: "bad_request",
    401: "authentication_required",
    403: "forbidden",
    404: "resource_not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    422: "validation_error",
    429: "rate_limited",
    502: "catalog_unavailable",
    503: "service_unavailable",
}


class CatalogNotConfiguredError(Exception):
    """The server has no usable TMDB credential."""


class CatalogNotFoundError(Exception):
    """The requested TMDB resource does not exist."""


class CatalogRateLimitedError(Exception):
    def __init__(self, retry_after: int = 30) -> None:
        self.retry_after = max(1, min(retry_after, 300))
        super().__init__("catalog rate limited")


class CatalogUpstreamError(Exception):
    """TMDB was unavailable or returned an invalid response."""


def _request_id(request: Request) -> str:
    state_request_id = getattr(request.state, "request_id", None)
    if isinstance(state_request_id, str):
        return state_request_id
    return get_request_id() or "unknown"


def _safe_headers(exception: StarletteHTTPException) -> dict[str, str]:
    if not exception.headers:
        return {}

    allowed = {"allow", "retry-after"}
    return {key: value for key, value in exception.headers.items() if key.lower() in allowed}


async def http_exception_handler(
    request: Request, exception: StarletteHTTPException
) -> JSONResponse:
    error_code = _HTTP_ERROR_CODES.get(exception.status_code, "request_error")
    return JSONResponse(
        status_code=exception.status_code,
        content={"error": error_code, "request_id": _request_id(request)},
        headers=_safe_headers(exception),
    )


async def validation_exception_handler(
    request: Request, _exception: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "request_id": _request_id(request)},
    )


async def catalog_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    status_code = 502
    error = "catalog_unavailable"
    headers: dict[str, str] = {}

    if isinstance(exception, CatalogNotConfiguredError):
        status_code = 503
        error = "catalog_not_configured"
    elif isinstance(exception, CatalogNotFoundError):
        status_code = 404
        error = "resource_not_found"
    elif isinstance(exception, CatalogRateLimitedError):
        status_code = 503
        error = "catalog_rate_limited"
        headers["Retry-After"] = str(exception.retry_after)

    return JSONResponse(
        status_code=status_code,
        content={"error": error, "request_id": _request_id(request)},
        headers=headers,
    )


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )
    for exception_type in (
        CatalogNotConfiguredError,
        CatalogNotFoundError,
        CatalogRateLimitedError,
        CatalogUpstreamError,
    ):
        app.add_exception_handler(
            exception_type,
            catalog_exception_handler,  # type: ignore[arg-type]
        )
