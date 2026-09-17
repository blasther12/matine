from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.core.auth import CurrentIdentity, get_current_identity
from app.modules.library.router import get_library_service
from app.modules.library.schemas import (
    LibraryMovieCreate,
    LibraryMovieListResponse,
    LibraryMovieResponse,
    LibraryMovieUpdate,
    MovieStatus,
)
from app.modules.library.service import LibraryService

_AUTH_USER_ID = UUID("1f7356ec-caa9-4c93-863a-95a6fa91340f")
_NOW = datetime(2026, 9, 17, tzinfo=UTC)


class FakeLibraryService:
    def __init__(self) -> None:
        self.last_identity: CurrentIdentity | None = None
        self.last_status: MovieStatus | None = None
        self.last_payload: LibraryMovieCreate | LibraryMovieUpdate | None = None
        self.deleted_tmdb_id: int | None = None

    async def list_movies(
        self, identity: CurrentIdentity, *, status: MovieStatus | None = None
    ) -> LibraryMovieListResponse:
        self.last_identity = identity
        self.last_status = status
        return LibraryMovieListResponse(items=[self._response(status or MovieStatus.WATCHLIST)])

    async def get_movie(self, identity: CurrentIdentity, tmdb_id: int) -> LibraryMovieResponse:
        self.last_identity = identity
        return self._response(MovieStatus.WATCHLIST, tmdb_id=tmdb_id)

    async def put_movie(
        self,
        identity: CurrentIdentity,
        tmdb_id: int,
        payload: LibraryMovieCreate,
    ) -> LibraryMovieResponse:
        self.last_identity = identity
        self.last_payload = payload
        return self._response(
            payload.status,
            tmdb_id=tmdb_id,
            rating=payload.rating,
            favorite=payload.favorite,
        )

    async def patch_movie(
        self,
        identity: CurrentIdentity,
        tmdb_id: int,
        payload: LibraryMovieUpdate,
    ) -> LibraryMovieResponse:
        self.last_identity = identity
        self.last_payload = payload
        return self._response(
            payload.status or MovieStatus.WATCHLIST,
            tmdb_id=tmdb_id,
            rating=payload.rating,
            favorite=payload.favorite or False,
        )

    async def delete_movie(self, identity: CurrentIdentity, tmdb_id: int) -> None:
        self.last_identity = identity
        self.deleted_tmdb_id = tmdb_id

    @staticmethod
    def _response(
        status: MovieStatus,
        *,
        tmdb_id: int = 550,
        rating: float | None = None,
        favorite: bool = False,
    ) -> LibraryMovieResponse:
        return LibraryMovieResponse(
            tmdb_id=tmdb_id,
            status=status,
            rating=rating,
            favorite=favorite,
            created_at=_NOW,
            updated_at=_NOW,
        )


@pytest.fixture
def authenticated_library_app(
    application: FastAPI,
) -> tuple[FastAPI, FakeLibraryService]:
    service = FakeLibraryService()

    async def identity_override() -> CurrentIdentity:
        return CurrentIdentity(auth_user_id=_AUTH_USER_ID)

    def service_override() -> LibraryService:
        return service  # type: ignore[return-value]

    application.dependency_overrides[get_current_identity] = identity_override
    application.dependency_overrides[get_library_service] = service_override
    return application, service


@pytest.mark.asyncio
async def test_library_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/me/movies")

    assert response.status_code == 401
    assert response.json()["error"] == "authentication_required"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "expected_status"),
    [("/me/movies", None), ("/me/watchlist", "WATCHLIST"), ("/me/watched", "WATCHED")],
)
async def test_library_lists_are_scoped_to_token_identity(
    authenticated_library_app: tuple[FastAPI, FakeLibraryService],
    client: AsyncClient,
    path: str,
    expected_status: str | None,
) -> None:
    _, service = authenticated_library_app
    response = await client.get(path)

    assert response.status_code == 200
    assert response.json()["items"][0]["tmdb_id"] == 550
    assert "user_id" not in response.text
    assert service.last_identity == CurrentIdentity(auth_user_id=_AUTH_USER_ID)
    assert service.last_status == expected_status


@pytest.mark.asyncio
async def test_create_rejects_client_ownership_claims(
    authenticated_library_app: tuple[FastAPI, FakeLibraryService],
    client: AsyncClient,
) -> None:
    _, service = authenticated_library_app
    response = await client.post(
        "/me/movies/550",
        json={
            "status": "WATCHLIST",
            "user_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        },
    )

    assert response.status_code == 422
    assert service.last_identity is None


@pytest.mark.asyncio
async def test_create_validates_half_star_rating(
    authenticated_library_app: tuple[FastAPI, FakeLibraryService],
    client: AsyncClient,
) -> None:
    _, service = authenticated_library_app
    invalid = await client.post("/me/movies/550", json={"status": "WATCHED", "rating": 4.2})
    valid = await client.post(
        "/me/movies/550",
        json={"status": "WATCHED", "rating": 4.5, "favorite": True},
    )

    assert invalid.status_code == 422
    assert valid.status_code == 201
    assert valid.json()["rating"] == 4.5
    assert valid.json()["favorite"] is True
    assert service.last_identity == CurrentIdentity(auth_user_id=_AUTH_USER_ID)


@pytest.mark.asyncio
async def test_patch_accepts_explicit_rating_removal(
    authenticated_library_app: tuple[FastAPI, FakeLibraryService],
    client: AsyncClient,
) -> None:
    _, service = authenticated_library_app
    response = await client.patch("/me/movies/550", json={"rating": None})

    assert response.status_code == 200
    assert isinstance(service.last_payload, LibraryMovieUpdate)
    assert "rating" in service.last_payload.model_fields_set


@pytest.mark.asyncio
async def test_patch_rejects_empty_or_null_required_changes(
    authenticated_library_app: tuple[FastAPI, FakeLibraryService],
    client: AsyncClient,
) -> None:
    empty = await client.patch("/me/movies/550", json={})
    null_status = await client.patch("/me/movies/550", json={"status": None})

    assert empty.status_code == 422
    assert null_status.status_code == 422


@pytest.mark.asyncio
async def test_delete_uses_token_identity(
    authenticated_library_app: tuple[FastAPI, FakeLibraryService],
    client: AsyncClient,
) -> None:
    _, service = authenticated_library_app
    response = await client.delete("/me/movies/550")

    assert response.status_code == 204
    assert response.content == b""
    assert service.deleted_tmdb_id == 550
    assert service.last_identity == CurrentIdentity(auth_user_id=_AUTH_USER_ID)
