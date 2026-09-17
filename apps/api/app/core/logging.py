import json
import logging
import re
import sys
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import Any

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

_SENSITIVE_HEADER = re.compile(r"(?i)\b(authorization|cookie|set-cookie)(\s*[:=]\s*)[^\r\n]+")
_SENSITIVE_PAIR = re.compile(
    r"(?i)\b(authorization|cookie|set-cookie|password|passwd|token|api[_-]?key|secret)"
    r"\b(\s*[:=]\s*)([^\s,;]+)"
)
_BEARER = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/-]+=*")
_JWT = re.compile(r"\beyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b")
_DATABASE_CREDENTIAL = re.compile(r"(?i)\b(postgresql(?:\+asyncpg)?://[^:\s/@]+):[^@\s/]+@")

_ALLOWED_EXTRA_FIELDS = (
    "request_id",
    "method",
    "route",
    "status",
    "duration_ms",
    "exception_type",
)


def redact_sensitive(value: str) -> str:
    redacted = _SENSITIVE_HEADER.sub(
        lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", value
    )
    redacted = _BEARER.sub("Bearer [REDACTED]", redacted)
    redacted = _JWT.sub("[REDACTED_JWT]", redacted)
    redacted = _DATABASE_CREDENTIAL.sub(r"\1:[REDACTED]@", redacted)
    return _SENSITIVE_PAIR.sub(
        lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", redacted
    )


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "logger": record.name,
            "event": redact_sensitive(record.getMessage()),
        }

        for field in _ALLOWED_EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = redact_sensitive(value) if isinstance(value, str) else value

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(level: str) -> None:
    root_logger = logging.getLogger()

    for handler in tuple(root_logger.handlers):
        if getattr(handler, "_movie_platform_handler", False):
            root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler._movie_platform_handler = True  # type: ignore[attr-defined]
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def set_request_id(request_id: str) -> Token[str | None]:
    return _request_id.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    _request_id.reset(token)


def get_request_id() -> str | None:
    return _request_id.get()
