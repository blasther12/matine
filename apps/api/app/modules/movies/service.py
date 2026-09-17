import re
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CatalogUpstreamError
from app.integrations.tmdb.client import TMDBClient
from app.integrations.tmdb.repository import ExternalCacheRepository
from app.integrations.tmdb.schemas import (
    TMDBMovieDetails,
    TMDBMovieSummary,
    TMDBProvider,
    TMDBRegionProviders,
)
from app.modules.movies.schemas import (
    CastMember,
    CrewMember,
    Genre,
    MovieCreditsResponse,
    MovieDetailsResponse,
    MovieProvidersResponse,
    MovieSearchItem,
    MovieSearchResponse,
    StreamingProvider,
    Trailer,
)

_PUBLIC_MODEL = TypeVar("_PUBLIC_MODEL", bound=BaseModel)
_IMAGE_PATH = re.compile(r"^/[A-Za-z0-9._/-]+$")
_VIDEO_KEY = re.compile(r"^[A-Za-z0-9_-]+$")


def _bounded(value: str, maximum: int, fallback: str = "") -> str:
    normalized = value.strip()
    return (normalized or fallback)[:maximum]


def _date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _image_path(value: str | None) -> str | None:
    if value is None or ".." in value or len(value) > 255 or _IMAGE_PATH.fullmatch(value) is None:
        return None
    return value


def _movie_item(movie: TMDBMovieSummary) -> MovieSearchItem:
    released = _date(movie.release_date)
    title = _bounded(movie.title, 500, "Untitled")
    return MovieSearchItem(
        tmdb_id=movie.id,
        title=title,
        original_title=_bounded(movie.original_title, 500, title),
        overview=_bounded(movie.overview, 10_000),
        release_date=released,
        year=released.year if released else None,
        poster_path=_image_path(movie.poster_path),
        vote_average=movie.vote_average,
    )


def _provider(provider: TMDBProvider) -> StreamingProvider:
    return StreamingProvider(
        tmdb_provider_id=provider.provider_id,
        name=_bounded(provider.provider_name, 300, "Provider"),
        logo_path=_image_path(provider.logo_path),
        display_priority=provider.display_priority,
    )


def _providers(values: list[TMDBProvider]) -> tuple[StreamingProvider, ...]:
    unique: dict[int, StreamingProvider] = {}
    for value in sorted(values, key=lambda item: item.display_priority):
        unique.setdefault(value.provider_id, _provider(value))
    return tuple(unique.values())


class MovieCatalogService:
    def __init__(self, session: AsyncSession, tmdb: TMDBClient) -> None:
        self._session = session
        self._tmdb = tmdb
        self._cache = ExternalCacheRepository(session)

    async def search(self, query: str, page: int) -> MovieSearchResponse:
        upstream = await self._tmdb.search_movies(query, page)
        return MovieSearchResponse(
            page=upstream.page,
            total_pages=upstream.total_pages,
            total_results=upstream.total_results,
            results=tuple(_movie_item(movie) for movie in upstream.results),
        )

    async def _cached(
        self,
        key: str,
        model: type[_PUBLIC_MODEL],
        ttl: timedelta,
        loader: Callable[[], Any],
    ) -> _PUBLIC_MODEL:
        payload = await self._cache.get("tmdb", key)
        if payload is not None:
            try:
                return model.model_validate(payload)
            except ValidationError:
                await self._cache.delete("tmdb", key)

        result = await loader()
        if not isinstance(result, model):
            raise CatalogUpstreamError
        await self._cache.put("tmdb", key, result.model_dump(mode="json"), ttl)
        await self._session.commit()
        return result

    async def details(self, tmdb_id: int) -> MovieDetailsResponse:
        async def load() -> MovieDetailsResponse:
            movie = await self._tmdb.movie_details(tmdb_id)
            return self._map_details(movie)

        return await self._cached(
            f"movie:details:v1:pt-BR:{tmdb_id}",
            MovieDetailsResponse,
            timedelta(hours=24),
            load,
        )

    def _map_details(self, movie: TMDBMovieDetails) -> MovieDetailsResponse:
        released = _date(movie.release_date)
        title = _bounded(movie.title, 500, "Untitled")
        trailer = None
        ordered_videos = sorted(
            movie.videos.results,
            key=lambda video: (
                video.site != "YouTube",
                video.type != "Trailer",
                not video.official,
            ),
        )
        for video in ordered_videos:
            if video.site == "YouTube" and _VIDEO_KEY.fullmatch(video.key):
                trailer = Trailer(
                    key=video.key,
                    name=_bounded(video.name, 500, "Trailer"),
                )
                break

        return MovieDetailsResponse(
            tmdb_id=movie.id,
            title=title,
            original_title=_bounded(movie.original_title, 500, title),
            overview=_bounded(movie.overview, 10_000),
            release_date=released,
            year=released.year if released else None,
            runtime_minutes=movie.runtime,
            poster_path=_image_path(movie.poster_path),
            backdrop_path=_image_path(movie.backdrop_path),
            vote_average=movie.vote_average,
            vote_count=movie.vote_count,
            genres=tuple(
                Genre(tmdb_id=genre.id, name=_bounded(genre.name, 100, "Genre"))
                for genre in movie.genres
            ),
            trailer=trailer,
        )

    async def credits(self, tmdb_id: int) -> MovieCreditsResponse:
        async def load() -> MovieCreditsResponse:
            credits = await self._tmdb.movie_credits(tmdb_id)
            cast = tuple(
                CastMember(
                    tmdb_id=member.id,
                    name=_bounded(member.name, 300, "Unknown"),
                    character=_bounded(member.character, 500),
                    profile_path=_image_path(member.profile_path),
                    order=member.order,
                )
                for member in sorted(credits.cast, key=lambda item: item.order)[:20]
            )
            crew = tuple(
                CrewMember(
                    tmdb_id=member.id,
                    name=_bounded(member.name, 300, "Unknown"),
                    job=_bounded(member.job, 300),
                    department=_bounded(member.department, 300),
                    profile_path=_image_path(member.profile_path),
                )
                for member in credits.crew[:50]
            )
            return MovieCreditsResponse(tmdb_id=credits.id, cast=cast, crew=crew)

        return await self._cached(
            f"movie:credits:v1:pt-BR:{tmdb_id}",
            MovieCreditsResponse,
            timedelta(days=7),
            load,
        )

    async def providers(self, tmdb_id: int) -> MovieProvidersResponse:
        async def load() -> MovieProvidersResponse:
            upstream = await self._tmdb.movie_providers(tmdb_id)
            region = upstream.results.get("BR", TMDBRegionProviders())
            return MovieProvidersResponse(
                tmdb_id=upstream.id,
                streaming=_providers(region.flatrate),
                free=_providers(region.free),
                ads=_providers(region.ads),
                rent=_providers(region.rent),
                buy=_providers(region.buy),
            )

        return await self._cached(
            f"movie:providers:v1:BR:{tmdb_id}",
            MovieProvidersResponse,
            timedelta(hours=6),
            load,
        )
