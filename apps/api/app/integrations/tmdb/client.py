from collections.abc import AsyncIterator
from typing import TypeVar

import httpx
from fastapi import Request
from pydantic import BaseModel, ValidationError

from app.core.errors import (
    CatalogNotConfiguredError,
    CatalogNotFoundError,
    CatalogRateLimitedError,
    CatalogUpstreamError,
)
from app.integrations.tmdb.schemas import (
    TMDBCreditsResponse,
    TMDBMovieDetails,
    TMDBProvidersResponse,
    TMDBSearchResponse,
)

_BASE_URL = "https://api.themoviedb.org/3"
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_ResponseModel = TypeVar("_ResponseModel", bound=BaseModel)


class TMDBClient:
    def __init__(self, token: str, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._token = token
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers={
                "Accept": "application/json",
                **({"Authorization": f"Bearer {token}"} if token else {}),
            },
            timeout=httpx.Timeout(8.0, connect=3.0, pool=2.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            follow_redirects=False,
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(
        self,
        path: str,
        *,
        params: dict[str, str | int | bool],
        response_model: type[_ResponseModel],
    ) -> _ResponseModel:
        if not self._token:
            raise CatalogNotConfiguredError

        try:
            response = await self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise CatalogUpstreamError from exc
        except httpx.HTTPError as exc:
            raise CatalogUpstreamError from exc

        if response.status_code == 404:
            raise CatalogNotFoundError
        if response.status_code == 429:
            retry_header = response.headers.get("Retry-After", "30")
            try:
                retry_after = int(retry_header)
            except ValueError:
                retry_after = 30
            raise CatalogRateLimitedError(retry_after)
        if response.status_code < 200 or response.status_code >= 300:
            raise CatalogUpstreamError
        if len(response.content) > _MAX_RESPONSE_BYTES:
            raise CatalogUpstreamError

        try:
            return response_model.model_validate_json(response.content)
        except ValidationError as exc:
            raise CatalogUpstreamError from exc

    async def search_movies(self, query: str, page: int) -> TMDBSearchResponse:
        return await self._get(
            "/search/movie",
            params={
                "query": query,
                "page": page,
                "language": "pt-BR",
                "region": "BR",
                "include_adult": "false",
            },
            response_model=TMDBSearchResponse,
        )

    async def movie_details(self, tmdb_id: int) -> TMDBMovieDetails:
        return await self._get(
            f"/movie/{tmdb_id}",
            params={"language": "pt-BR", "append_to_response": "videos"},
            response_model=TMDBMovieDetails,
        )

    async def movie_credits(self, tmdb_id: int) -> TMDBCreditsResponse:
        return await self._get(
            f"/movie/{tmdb_id}/credits",
            params={"language": "pt-BR"},
            response_model=TMDBCreditsResponse,
        )

    async def movie_providers(self, tmdb_id: int) -> TMDBProvidersResponse:
        return await self._get(
            f"/movie/{tmdb_id}/watch/providers",
            params={},
            response_model=TMDBProvidersResponse,
        )


async def get_tmdb_client(request: Request) -> AsyncIterator[TMDBClient]:
    client = TMDBClient(request.app.state.settings.tmdb_token)
    try:
        yield client
    finally:
        await client.close()
