import json
import logging
from typing import Annotated
from uuid import UUID

import pytest
from fastapi import FastAPI, Query
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.logging import JsonFormatter, redact_sensitive
from app.main import create_app

_EXPECTED_SECURITY_HEADERS = {
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    "permissions-policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "referrer-policy": "no-referrer",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
}


def _assert_request_id(value: str) -> None:
    parsed = UUID(value)
    assert parsed.version == 4


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/health", "/does-not-exist"])
async def test_security_headers_cover_success_and_errors(client: AsyncClient, path: str) -> None:
    response = await client.get(path)

    for name, expected_value in _EXPECTED_SECURITY_HEADERS.items():
        assert response.headers[name] == expected_value

    assert response.headers["cache-control"] == "no-store"
    _assert_request_id(response.headers["x-request-id"])
    assert "strict-transport-security" not in response.headers


@pytest.mark.asyncio
async def test_request_ids_are_server_generated_and_unique(client: AsyncClient) -> None:
    attacker_value = "attacker-controlled-id"
    first = await client.get("/health", headers={"X-Request-ID": attacker_value})
    second = await client.get("/health")

    first_request_id = first.headers["x-request-id"]
    second_request_id = second.headers["x-request-id"]
    _assert_request_id(first_request_id)
    _assert_request_id(second_request_id)
    assert first_request_id != attacker_value
    assert first_request_id != second_request_id


@pytest.mark.asyncio
async def test_not_found_uses_public_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/missing")

    assert response.status_code == 404
    assert response.json() == {
        "error": "resource_not_found",
        "request_id": response.headers["x-request-id"],
    }


@pytest.mark.asyncio
async def test_validation_error_does_not_echo_rejected_input(
    application: FastAPI,
) -> None:
    async def validated_route(
        limit: Annotated[int, Query(ge=1, le=10)],
    ) -> dict[str, int]:
        return {"limit": limit}

    application.add_api_route(
        "/_test/validated",
        validated_route,
        methods=["GET"],
        include_in_schema=False,
    )
    transport = ASGITransport(app=application)

    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        response = await test_client.get("/_test/validated?limit=private-input")

    assert response.status_code == 422
    assert response.json() == {
        "error": "validation_error",
        "request_id": response.headers["x-request-id"],
    }
    assert "private-input" not in response.text


@pytest.mark.asyncio
async def test_unhandled_error_is_sanitized(
    application: FastAPI, caplog: pytest.LogCaptureFixture
) -> None:
    secret = "do-not-leak-this-value"

    async def failing_route() -> None:
        raise RuntimeError(f"internal failure token={secret}")

    application.add_api_route(
        "/_test/failure",
        failing_route,
        methods=["GET"],
        include_in_schema=False,
    )
    transport = ASGITransport(app=application)

    with caplog.at_level(logging.INFO, logger="app.http"):
        async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
            response = await test_client.get("/_test/failure")

    assert response.status_code == 500
    assert response.json() == {
        "error": "internal_error",
        "request_id": response.headers["x-request-id"],
    }
    assert secret not in response.text
    assert secret not in " ".join(record.getMessage() for record in caplog.records)
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.asyncio
async def test_cors_uses_an_exact_allowlist(client: AsyncClient) -> None:
    allowed = await client.get("/health", headers={"Origin": "http://localhost:3000"})
    denied = await client.get("/health", headers={"Origin": "https://attacker.example"})

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-credentials" not in allowed.headers
    assert "access-control-allow-origin" not in denied.headers


@pytest.mark.asyncio
async def test_cors_preflight_allows_only_configured_read_route(client: AsyncClient) -> None:
    response = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Request-ID",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-methods"] == "GET, POST, PATCH, DELETE"


@pytest.mark.asyncio
async def test_untrusted_host_is_rejected_with_safe_json(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"Host": "attacker.example"})

    assert response.status_code == 400
    assert response.json() == {
        "error": "invalid_host",
        "request_id": response.headers["x-request-id"],
    }
    assert "attacker.example" not in response.text
    assert response.headers["x-frame-options"] == "DENY"


@pytest.mark.asyncio
async def test_logs_use_route_template_and_omit_query_and_headers(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    query_secret = "private-search-value"
    authorization_secret = "private-bearer-value"

    with caplog.at_level(logging.INFO, logger="app.http"):
        await client.get(
            f"/health?q={query_secret}",
            headers={"Authorization": f"Bearer {authorization_secret}"},
        )

    request_records = [
        record
        for record in caplog.records
        if record.name == "app.http" and record.getMessage() == "http_request"
    ]
    assert request_records
    assert request_records[-1].route == "/health"
    serialized_records = " ".join(str(record.__dict__) for record in request_records)
    assert query_secret not in serialized_records
    assert authorization_secret not in serialized_records


def test_log_redaction_covers_common_secret_shapes() -> None:
    values = {
        "bearer-secret": "Authorization: Bearer bearer-secret",
        "cookie-secret": "Cookie=cookie-secret",
        "api-key-secret": "api_key=api-key-secret",
        "database-secret": (
            "postgresql+asyncpg://movie_platform:database-secret@localhost:5432/app"
        ),
        "eyJhbGciOiJIUzI1NiJ9.payload.signature": "eyJhbGciOiJIUzI1NiJ9.payload.signature",
    }

    redacted = redact_sensitive(" ".join(values.values()))

    for secret in values:
        assert secret not in redacted


def test_json_formatter_emits_only_safe_structured_fields() -> None:
    record = logging.LogRecord(
        name="app.http",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="http_request",
        args=(),
        exc_info=None,
    )
    record.request_id = "safe-request-id"
    record.route = "/health"
    record.method = "GET"
    record.status = 200
    record.duration_ms = 1.25
    record.private_value = "must-not-be-serialized"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["event"] == "http_request"
    assert payload["route"] == "/health"
    assert "private_value" not in payload


@pytest.mark.asyncio
async def test_hsts_is_only_emitted_for_production_https() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        debug=False,
        database_url=("postgresql+asyncpg://api:strong-local-placeholder@db.internal:5432/app"),
        cors_origins_csv="https://web.example.com",
        trusted_hosts_csv="api.example.com",
        tmdb_api_key="synthetic-test-token",
        supabase_url="https://project.supabase.co",
        supabase_anon_key="synthetic-anon-key",
    )
    production_app = create_app(settings)
    transport = ASGITransport(app=production_app)

    async with AsyncClient(transport=transport, base_url="https://api.example.com") as https_client:
        https_response = await https_client.get("/health")
    async with AsyncClient(transport=transport, base_url="http://api.example.com") as http_client:
        http_response = await http_client.get("/health")

    assert https_response.headers["strict-transport-security"] == "max-age=31536000"
    assert "strict-transport-security" not in http_response.headers


@pytest.mark.asyncio
async def test_production_disables_interactive_api_docs() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        database_url=("postgresql+asyncpg://api:strong-local-placeholder@db.internal:5432/app"),
        cors_origins_csv="https://web.example.com",
        trusted_hosts_csv="api.example.com",
        tmdb_api_key="synthetic-test-token",
        supabase_url="https://project.supabase.co",
        supabase_anon_key="synthetic-anon-key",
    )
    production_app = create_app(settings)
    transport = ASGITransport(app=production_app)

    async with AsyncClient(
        transport=transport, base_url="https://api.example.com"
    ) as production_client:
        response = await production_client.get("/docs")

    assert response.status_code == 404
    assert response.json()["error"] == "resource_not_found"
