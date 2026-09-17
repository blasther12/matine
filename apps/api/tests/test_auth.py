from typing import Annotated
from uuid import UUID

import pytest
import respx
from fastapi import Depends, FastAPI
from httpx import AsyncClient, Response
from pydantic import SecretStr

from app.core.auth import CurrentIdentity, get_current_identity


@pytest.mark.asyncio
async def test_missing_bearer_token_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/me")

    assert response.status_code == 401
    assert response.json()["error"] == "authentication_required"


@pytest.mark.asyncio
@respx.mock
async def test_supabase_user_endpoint_validates_identity(
    application: FastAPI,
    client: AsyncClient,
) -> None:
    auth_user_id = UUID("ec05ac7d-6b47-4dd2-86bd-e54fa6d968c3")
    application.state.settings.supabase_url = "https://project.supabase.co"
    application.state.settings.supabase_anon_key = SecretStr("synthetic-anon-key")
    respx.get("https://project.supabase.co/auth/v1/user").mock(
        return_value=Response(200, json={"id": str(auth_user_id)})
    )

    async def identity_route(
        identity: Annotated[CurrentIdentity, Depends(get_current_identity)],
    ) -> dict[str, str]:
        return {"id": str(identity.auth_user_id)}

    application.add_api_route("/_test/identity", identity_route, methods=["GET"])
    response = await client.get(
        "/_test/identity",
        headers={"Authorization": "Bearer opaque-supabase-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"id": str(auth_user_id)}
    request = respx.calls.last.request
    assert request.headers["apikey"] == "synthetic-anon-key"
    assert request.headers["authorization"] == "Bearer opaque-supabase-token"


@pytest.mark.asyncio
@respx.mock
async def test_rejected_supabase_token_returns_generic_401(
    application: FastAPI,
    client: AsyncClient,
) -> None:
    application.state.settings.supabase_url = "https://project.supabase.co"
    application.state.settings.supabase_anon_key = SecretStr("synthetic-anon-key")
    respx.get("https://project.supabase.co/auth/v1/user").mock(
        return_value=Response(401, json={"message": "private upstream detail"})
    )

    response = await client.get(
        "/me",
        headers={"Authorization": "Bearer rejected-token"},
    )

    assert response.status_code == 401
    assert response.json()["error"] == "authentication_required"
    assert "private upstream detail" not in response.text
