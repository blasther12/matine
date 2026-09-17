import unicodedata
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.rate_limit import enforce_catalog_rate_limit
from app.integrations.tmdb.client import TMDBClient, get_tmdb_client
from app.modules.movies.schemas import (
    MAX_TMDB_ID,
    MovieCreditsResponse,
    MovieDetailsResponse,
    MovieProvidersResponse,
    MovieSearchResponse,
)
from app.modules.movies.service import MovieCatalogService

router = APIRouter(
    prefix="/movies",
    tags=["movies"],
    dependencies=[Depends(enforce_catalog_rate_limit)],
)


def get_movie_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    tmdb: Annotated[TMDBClient, Depends(get_tmdb_client)],
) -> MovieCatalogService:
    return MovieCatalogService(session, tmdb)


def _normalized_query(value: str) -> str:
    query = value.strip()
    contains_control = any(unicodedata.category(character).startswith("C") for character in query)
    if len(query) < 2 or contains_control:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)
    return query


@router.get("/search", response_model=MovieSearchResponse)
async def search_movies(
    service: Annotated[MovieCatalogService, Depends(get_movie_service)],
    q: Annotated[str, Query(min_length=2, max_length=100)],
    page: Annotated[int, Query(ge=1, le=500)] = 1,
) -> MovieSearchResponse:
    return await service.search(_normalized_query(q), page)


@router.get("/{tmdb_id}", response_model=MovieDetailsResponse)
async def movie_details(
    service: Annotated[MovieCatalogService, Depends(get_movie_service)],
    response: Response,
    tmdb_id: Annotated[int, Path(ge=1, le=MAX_TMDB_ID)],
) -> MovieDetailsResponse:
    response.headers["Cache-Control"] = "public, max-age=300"
    return await service.details(tmdb_id)


@router.get("/{tmdb_id}/credits", response_model=MovieCreditsResponse)
async def movie_credits(
    service: Annotated[MovieCatalogService, Depends(get_movie_service)],
    response: Response,
    tmdb_id: Annotated[int, Path(ge=1, le=MAX_TMDB_ID)],
) -> MovieCreditsResponse:
    response.headers["Cache-Control"] = "public, max-age=300"
    return await service.credits(tmdb_id)


@router.get("/{tmdb_id}/providers", response_model=MovieProvidersResponse)
async def movie_providers(
    service: Annotated[MovieCatalogService, Depends(get_movie_service)],
    response: Response,
    tmdb_id: Annotated[int, Path(ge=1, le=MAX_TMDB_ID)],
) -> MovieProvidersResponse:
    response.headers["Cache-Control"] = "public, max-age=300"
    return await service.providers(tmdb_id)
