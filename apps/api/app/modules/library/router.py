from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentIdentity, get_current_identity
from app.core.database import get_session
from app.modules.library.schemas import (
    LibraryMovieCreate,
    LibraryMovieListResponse,
    LibraryMovieResponse,
    LibraryMovieUpdate,
    MovieStatus,
)
from app.modules.library.service import (
    LibraryEntryNotFoundError,
    LibraryProfileNotFoundError,
    LibraryService,
)

router = APIRouter(prefix="/me", tags=["library"])
TmdbId = Annotated[int, Path(gt=0, le=2_147_483_647)]


def get_library_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LibraryService:
    return LibraryService(session)


async def _list(
    identity: CurrentIdentity,
    service: LibraryService,
    status_filter: MovieStatus | None,
) -> LibraryMovieListResponse:
    try:
        return await service.list_movies(identity, status=status_filter)
    except LibraryProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.get("/movies", response_model=LibraryMovieListResponse)
async def list_movies(
    identity: Annotated[CurrentIdentity, Depends(get_current_identity)],
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> LibraryMovieListResponse:
    return await _list(identity, service, None)


@router.get("/watchlist", response_model=LibraryMovieListResponse)
async def list_watchlist(
    identity: Annotated[CurrentIdentity, Depends(get_current_identity)],
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> LibraryMovieListResponse:
    return await _list(identity, service, MovieStatus.WATCHLIST)


@router.get("/watched", response_model=LibraryMovieListResponse)
async def list_watched(
    identity: Annotated[CurrentIdentity, Depends(get_current_identity)],
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> LibraryMovieListResponse:
    return await _list(identity, service, MovieStatus.WATCHED)


@router.get("/movies/{tmdb_id}", response_model=LibraryMovieResponse)
async def get_movie(
    tmdb_id: TmdbId,
    identity: Annotated[CurrentIdentity, Depends(get_current_identity)],
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> LibraryMovieResponse:
    try:
        return await service.get_movie(identity, tmdb_id)
    except (LibraryProfileNotFoundError, LibraryEntryNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.post(
    "/movies/{tmdb_id}",
    response_model=LibraryMovieResponse,
    status_code=status.HTTP_201_CREATED,
)
async def put_movie(
    tmdb_id: TmdbId,
    payload: LibraryMovieCreate,
    identity: Annotated[CurrentIdentity, Depends(get_current_identity)],
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> LibraryMovieResponse:
    try:
        return await service.put_movie(identity, tmdb_id, payload)
    except LibraryProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.patch("/movies/{tmdb_id}", response_model=LibraryMovieResponse)
async def patch_movie(
    tmdb_id: TmdbId,
    payload: LibraryMovieUpdate,
    identity: Annotated[CurrentIdentity, Depends(get_current_identity)],
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> LibraryMovieResponse:
    try:
        return await service.patch_movie(identity, tmdb_id, payload)
    except (LibraryProfileNotFoundError, LibraryEntryNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.delete("/movies/{tmdb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    tmdb_id: TmdbId,
    identity: Annotated[CurrentIdentity, Depends(get_current_identity)],
    service: Annotated[LibraryService, Depends(get_library_service)],
) -> Response:
    try:
        await service.delete_movie(identity, tmdb_id)
    except (LibraryProfileNotFoundError, LibraryEntryNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
