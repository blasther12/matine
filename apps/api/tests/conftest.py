from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        debug=False,
        log_level="INFO",
        database_url=(
            "postgresql+asyncpg://movie_platform:movie_platform@localhost:5432/movie_platform_test"
        ),
        cors_origins_csv="http://localhost:3000",
        trusted_hosts_csv="testserver,localhost,127.0.0.1",
    )


@pytest.fixture
def application(test_settings: Settings) -> FastAPI:
    return create_app(test_settings)


@pytest.fixture
async def client(application: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
