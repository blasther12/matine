from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.core.auth import CurrentIdentity, get_current_identity
from app.modules.users.router import get_user_service
from app.modules.users.schemas import ProfileCreate, UserResponse
from app.modules.users.service import UserService

_AUTH_USER_ID = UUID("1f7356ec-caa9-4c93-863a-95a6fa91340f")
_PROFILE_ID = UUID("3bc979dd-0e85-4c0a-8a9e-0234bb02dad2")
_NOW = datetime(2026, 9, 17, tzinfo=UTC)


class FakeUserService:
    def __init__(self) -> None:
        self.last_identity: CurrentIdentity | None = None

    async def me(self, identity: CurrentIdentity) -> UserResponse:
        self.last_identity = identity
        return self._response()

    async def create_profile(
        self, identity: CurrentIdentity, payload: ProfileCreate
    ) -> UserResponse:
        self.last_identity = identity
        return self._response(username=payload.username, display_name=payload.display_name)

    @staticmethod
    def _response(username: str = "cinefilo", display_name: str = "Cinéfilo") -> UserResponse:
        return UserResponse(
            id=_PROFILE_ID,
            username=username,
            display_name=display_name,
            avatar_url=None,
            created_at=_NOW,
            updated_at=_NOW,
        )


@pytest.fixture
def authenticated_app(application: FastAPI) -> tuple[FastAPI, FakeUserService]:
    service = FakeUserService()

    async def identity_override() -> CurrentIdentity:
        return CurrentIdentity(auth_user_id=_AUTH_USER_ID)

    def service_override() -> UserService:
        return service  # type: ignore[return-value]

    application.dependency_overrides[get_current_identity] = identity_override
    application.dependency_overrides[get_user_service] = service_override
    return application, service


@pytest.mark.asyncio
async def test_me_returns_only_public_profile_fields(
    authenticated_app: tuple[FastAPI, FakeUserService],
    client: AsyncClient,
) -> None:
    _, service = authenticated_app
    response = await client.get("/me")

    assert response.status_code == 200
    assert response.json()["username"] == "cinefilo"
    assert "auth_user_id" not in response.json()
    assert service.last_identity == CurrentIdentity(auth_user_id=_AUTH_USER_ID)


@pytest.mark.asyncio
async def test_create_profile_rejects_client_ownership_claims(
    authenticated_app: tuple[FastAPI, FakeUserService],
    client: AsyncClient,
) -> None:
    _, service = authenticated_app
    response = await client.post(
        "/me",
        json={
            "username": "Cinema_Fan",
            "display_name": "Cinema Fan",
            "auth_user_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        },
    )

    assert response.status_code == 422
    assert service.last_identity is None


@pytest.mark.asyncio
async def test_create_profile_normalizes_username(
    authenticated_app: tuple[FastAPI, FakeUserService],
    client: AsyncClient,
) -> None:
    _, service = authenticated_app
    response = await client.post(
        "/me",
        json={"username": "Cinema_Fan", "display_name": "Cinema Fan"},
    )

    assert response.status_code == 201
    assert response.json()["username"] == "cinema_fan"
    assert service.last_identity == CurrentIdentity(auth_user_id=_AUTH_USER_ID)
