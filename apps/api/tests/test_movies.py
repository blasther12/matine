from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.database import Base, get_session
from app.integrations.tmdb.models import ExternalCache
from app.integrations.tmdb.repository import ExternalCacheRepository
from app.main import create_app
from app.modules.movies.router import get_movie_service
from app.modules.movies.schemas import MovieSearchResponse

TMDB_ROOT = "https://api.themoviedb.org/3"


@pytest.fixture
async def catalog_app() -> AsyncIterator[tuple[FastAPI, async_sessionmaker[AsyncSession]]]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url="postgresql+asyncpg://movie:movie@localhost/movie_test",
        cors_origins_csv="http://localhost:3000",
        trusted_hosts_csv="testserver",
        tmdb_api_key="synthetic-tmdb-token",
        rate_limit_requests=100,
    )
    application = create_app(settings)

    async def session_override() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    application.dependency_overrides[get_session] = session_override
    try:
        yield application, factory
    finally:
        await engine.dispose()


@pytest.fixture
async def catalog_client(
    catalog_app: tuple[FastAPI, async_sessionmaker[AsyncSession]],
) -> AsyncIterator[tuple[AsyncClient, async_sessionmaker[AsyncSession]]]:
    application, factory = catalog_app
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, factory


def movie_summary() -> dict[str, object]:
    return {
        "id": 348,
        "title": "Alien, o Oitavo Passageiro",
        "original_title": "Alien",
        "overview": "No espaço, ninguém pode ouvir você gritar.",
        "release_date": "1979-05-25",
        "poster_path": "/alien.jpg",
        "vote_average": 8.2,
    }


def movie_details() -> dict[str, object]:
    return {
        **movie_summary(),
        "runtime": 117,
        "backdrop_path": "/alien-backdrop.jpg",
        "vote_count": 15000,
        "genres": [{"id": 27, "name": "Terror"}],
        "videos": {
            "results": [
                {
                    "key": "LjLamj-b0I8",
                    "name": "Official Trailer",
                    "site": "YouTube",
                    "type": "Trailer",
                    "official": True,
                }
            ]
        },
    }


@pytest.mark.asyncio
@respx.mock
async def test_search_uses_bearer_header_and_never_persists_query(
    catalog_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = catalog_client
    upstream = respx.get(f"{TMDB_ROOT}/search/movie").mock(
        return_value=httpx.Response(
            200,
            json={"page": 1, "total_pages": 1, "total_results": 1, "results": [movie_summary()]},
        )
    )

    response = await client.get("/movies/search", params={"q": "  Alien  "})

    assert response.status_code == 200
    assert response.json()["results"][0]["tmdb_id"] == 348
    request = upstream.calls[0].request
    assert request.headers["Authorization"] == "Bearer synthetic-tmdb-token"
    assert request.url.params["query"] == "Alien"
    assert request.url.params["language"] == "pt-BR"
    assert request.url.params["region"] == "BR"
    assert request.url.params["include_adult"] == "false"
    assert "api_key" not in request.url.params
    assert "synthetic-tmdb-token" not in str(request.url)

    async with factory() as session:
        count = await session.scalar(select(func.count()).select_from(ExternalCache))
    assert count == 0


@pytest.mark.asyncio
@respx.mock
async def test_details_are_normalized_and_cached(
    catalog_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = catalog_client
    upstream = respx.get(f"{TMDB_ROOT}/movie/348").mock(
        return_value=httpx.Response(200, json=movie_details())
    )

    first = await client.get("/movies/348")
    second = await client.get("/movies/348")

    assert first.status_code == 200
    assert second.status_code == 200
    assert upstream.call_count == 1
    payload = second.json()
    assert payload["runtime_minutes"] == 117
    assert payload["trailer"]["key"] == "LjLamj-b0I8"
    assert payload["attribution"]["source"] == "TMDB"
    assert second.headers["cache-control"] == "public, max-age=300"

    async with factory() as session:
        entry = await session.get(
            ExternalCache,
            ("tmdb", "movie:details:v1:pt-BR:348"),
        )
        assert entry is not None
        assert "synthetic-tmdb-token" not in str(entry.payload)


@pytest.mark.asyncio
@respx.mock
async def test_credits_are_bounded_and_user_text_stays_plain_text(
    catalog_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _factory = catalog_client
    cast = [
        {
            "id": index + 1,
            "name": "<script>alert(1)</script>" if index == 0 else f"Actor {index}",
            "character": f"Character {index}",
            "order": index,
        }
        for index in range(25)
    ]
    respx.get(f"{TMDB_ROOT}/movie/348/credits").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 348,
                "cast": cast,
                "crew": [{"id": 50, "name": "Ridley Scott", "job": "Director"}],
            },
        )
    )

    response = await client.get("/movies/348/credits")

    assert response.status_code == 200
    assert len(response.json()["cast"]) == 20
    assert response.json()["cast"][0]["name"] == "<script>alert(1)</script>"


@pytest.mark.asyncio
@respx.mock
async def test_providers_use_only_br_and_required_categories(
    catalog_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _factory = catalog_client
    respx.get(f"{TMDB_ROOT}/movie/348/watch/providers").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 348,
                "results": {
                    "US": {"flatrate": [{"provider_id": 9, "provider_name": "US only"}]},
                    "BR": {
                        "flatrate": [
                            {
                                "provider_id": 8,
                                "provider_name": "Netflix",
                                "logo_path": "/netflix.jpg",
                                "display_priority": 1,
                            }
                        ],
                        "rent": [],
                    },
                },
            },
        )
    )

    response = await client.get("/movies/348/providers")

    assert response.status_code == 200
    payload = response.json()
    assert payload["region"] == "BR"
    assert [provider["name"] for provider in payload["streaming"]] == ["Netflix"]
    assert payload["free"] == []
    assert payload["availability_attribution"]["source"] == "JustWatch"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "expected_status"),
    [
        ("/movies/search?q=a", 422),
        ("/movies/search?q=ab%00cd", 422),
        ("/movies/search?q=valid&page=501", 422),
        ("/movies/0", 422),
        ("/movies/2147483648", 422),
    ],
)
async def test_catalog_input_is_bounded(
    catalog_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
    path: str,
    expected_status: int,
) -> None:
    client, _factory = catalog_client
    response = await client.get(path)
    assert response.status_code == expected_status
    assert response.json()["error"] == "validation_error"


@pytest.mark.asyncio
@respx.mock
async def test_upstream_errors_are_sanitized(
    catalog_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _factory = catalog_client
    respx.get(f"{TMDB_ROOT}/movie/348").mock(
        return_value=httpx.Response(500, text="secret upstream stack")
    )

    response = await client.get("/movies/348")

    assert response.status_code == 502
    assert response.json()["error"] == "catalog_unavailable"
    assert "secret" not in response.text
    assert "synthetic-tmdb-token" not in response.text


@pytest.mark.asyncio
@respx.mock
async def test_upstream_rate_limit_is_bounded_and_sanitized(
    catalog_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _factory = catalog_client
    respx.get(f"{TMDB_ROOT}/movie/348").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "999999"})
    )

    response = await client.get("/movies/348")

    assert response.status_code == 503
    assert response.json()["error"] == "catalog_rate_limited"
    assert response.headers["retry-after"] == "300"


@pytest.mark.asyncio
async def test_catalog_rate_limit_is_enforced_without_persisting_client_ip() -> None:
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url="postgresql+asyncpg://movie:movie@localhost/movie_test",
        cors_origins_csv="http://localhost:3000",
        trusted_hosts_csv="testserver",
        tmdb_api_key="synthetic-tmdb-token",
        rate_limit_requests=1,
        rate_limit_window_seconds=60,
    )
    application = create_app(settings)

    class FakeService:
        async def search(self, _query: str, _page: int) -> MovieSearchResponse:
            return MovieSearchResponse(page=1, total_pages=0, total_results=0, results=())

    application.dependency_overrides[get_movie_service] = FakeService
    transport = ASGITransport(app=application, client=("203.0.113.42", 12345))
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        first = await client.get("/movies/search", params={"q": "Alien"})
        second = await client.get("/movies/search", params={"q": "Alien"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error"] == "rate_limited"
    assert "203.0.113.42" not in repr(application.state.catalog_rate_limiter._windows)


@pytest.mark.asyncio
async def test_expired_cache_is_not_returned() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        session.add(
            ExternalCache(
                provider="tmdb",
                cache_key="expired",
                payload={"value": "old"},
                expires_at=datetime.now(UTC) - timedelta(seconds=1),
            )
        )
        await session.commit()
        repository = ExternalCacheRepository(session)
        assert await repository.get("tmdb", "expired") is None
    await engine.dispose()
