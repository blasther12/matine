from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentIdentity, get_current_identity
from app.core.database import get_session
from app.modules.experience.schemas import (
    CircleCreate,
    CircleMemberCreate,
    CircleResponse,
    DiaryCreate,
    DiaryEntryResponse,
    FeedItem,
    FollowCreate,
    MatchItem,
    MovieListCreate,
    MovieListItemCreate,
    MovieListResponse,
    MovieNightCandidateCreate,
    MovieNightCreate,
    MovieNightResponse,
    MovieNightVoteCreate,
    RecommendationItem,
    ReviewResponse,
    ReviewUpsert,
    StatsResponse,
    StreamingPreferences,
    WrappedResponse,
)
from app.modules.experience.service import (
    ExperienceForbiddenError,
    ExperienceNotFoundError,
    ExperienceProfileNotFoundError,
    ExperienceService,
)

router = APIRouter(tags=["experience"])


def get_experience_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExperienceService:
    return ExperienceService(session)


Identity = Annotated[CurrentIdentity, Depends(get_current_identity)]
Service = Annotated[ExperienceService, Depends(get_experience_service)]


def _not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND)


def _forbidden(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@router.get("/me/diary", response_model=list[DiaryEntryResponse])
async def list_diary(identity: Identity, service: Service) -> list[DiaryEntryResponse]:
    try:
        return await service.diary(identity)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.post(
    "/me/diary",
    response_model=DiaryEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_diary(
    payload: DiaryCreate, identity: Identity, service: Service
) -> DiaryEntryResponse:
    try:
        return await service.add_diary(identity, payload)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.get("/me/reviews", response_model=list[ReviewResponse])
async def list_reviews(identity: Identity, service: Service) -> list[ReviewResponse]:
    try:
        return await service.reviews(identity)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.post("/me/reviews", response_model=ReviewResponse)
async def save_review(
    payload: ReviewUpsert, identity: Identity, service: Service
) -> ReviewResponse:
    try:
        return await service.save_review(identity, payload)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.get("/me/lists", response_model=list[MovieListResponse])
async def list_lists(identity: Identity, service: Service) -> list[MovieListResponse]:
    try:
        return await service.lists(identity)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.post(
    "/me/lists",
    response_model=MovieListResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_list(
    payload: MovieListCreate, identity: Identity, service: Service
) -> MovieListResponse:
    try:
        return await service.create_list(identity, payload)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.post("/me/lists/{list_id}/items", status_code=status.HTTP_204_NO_CONTENT)
async def add_list_item(
    list_id: UUID,
    payload: MovieListItemCreate,
    identity: Identity,
    service: Service,
) -> Response:
    try:
        await service.add_list_item(identity, list_id, payload)
    except (ExperienceProfileNotFoundError, ExperienceNotFoundError) as exc:
        raise _not_found(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/social/follow", status_code=status.HTTP_204_NO_CONTENT)
async def follow(
    payload: FollowCreate, identity: Identity, service: Service
) -> Response:
    try:
        await service.follow(identity, payload)
    except (ExperienceProfileNotFoundError, ExperienceNotFoundError) as exc:
        raise _not_found(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/social/feed", response_model=list[FeedItem])
async def feed(identity: Identity, service: Service) -> list[FeedItem]:
    try:
        return await service.feed(identity)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.get("/me/streaming", response_model=StreamingPreferences)
async def get_streaming(identity: Identity, service: Service) -> StreamingPreferences:
    try:
        return await service.streaming(identity)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.post("/me/streaming", response_model=StreamingPreferences)
async def save_streaming(
    payload: StreamingPreferences, identity: Identity, service: Service
) -> StreamingPreferences:
    try:
        return await service.save_streaming(identity, payload)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.get("/me/circles", response_model=list[CircleResponse])
async def list_circles(identity: Identity, service: Service) -> list[CircleResponse]:
    try:
        return await service.circles(identity)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.post(
    "/me/circles",
    response_model=CircleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_circle(
    payload: CircleCreate, identity: Identity, service: Service
) -> CircleResponse:
    try:
        return await service.create_circle(identity, payload)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.post(
    "/me/circles/{circle_id}/members",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def add_circle_member(
    circle_id: UUID,
    payload: CircleMemberCreate,
    identity: Identity,
    service: Service,
) -> Response:
    try:
        await service.add_circle_member(identity, circle_id, payload)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc
    except ExperienceForbiddenError as exc:
        raise _forbidden(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/circles/{circle_id}/match", response_model=list[MatchItem])
async def movie_match(
    circle_id: UUID, identity: Identity, service: Service
) -> list[MatchItem]:
    try:
        return await service.match(identity, circle_id)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc
    except ExperienceForbiddenError as exc:
        raise _forbidden(exc) from exc


@router.post(
    "/me/circles/{circle_id}/movie-nights",
    response_model=MovieNightResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie_night(
    circle_id: UUID,
    payload: MovieNightCreate,
    identity: Identity,
    service: Service,
) -> MovieNightResponse:
    try:
        return await service.create_night(identity, circle_id, payload)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc
    except ExperienceForbiddenError as exc:
        raise _forbidden(exc) from exc


@router.post(
    "/me/movie-nights/{night_id}/candidates",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def add_movie_night_candidate(
    night_id: UUID,
    payload: MovieNightCandidateCreate,
    identity: Identity,
    service: Service,
) -> Response:
    try:
        await service.add_candidate(identity, night_id, payload)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc
    except ExperienceForbiddenError as exc:
        raise _forbidden(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/me/movie-nights/{night_id}/vote",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def vote_movie_night(
    night_id: UUID,
    payload: MovieNightVoteCreate,
    identity: Identity,
    service: Service,
) -> Response:
    try:
        await service.vote(identity, night_id, payload)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc
    except ExperienceForbiddenError as exc:
        raise _forbidden(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me/movie-nights/{night_id}",
    response_model=MovieNightResponse,
)
async def movie_night(
    night_id: UUID, identity: Identity, service: Service
) -> MovieNightResponse:
    try:
        return await service.night(identity, night_id)
    except (ExperienceProfileNotFoundError, ExperienceNotFoundError) as exc:
        raise _not_found(exc) from exc


@router.get("/me/recommendations", response_model=list[RecommendationItem])
async def recommendations(
    identity: Identity, service: Service
) -> list[RecommendationItem]:
    try:
        return await service.recommendations(identity)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.get("/me/stats", response_model=StatsResponse)
async def stats(identity: Identity, service: Service) -> StatsResponse:
    try:
        return await service.stats(identity)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc


@router.get("/me/wrapped", response_model=WrappedResponse)
async def wrapped(
    identity: Identity,
    service: Service,
    year: Annotated[
        int,
        Query(ge=2000, le=datetime.now(UTC).year),
    ] = datetime.now(UTC).year,
) -> WrappedResponse:
    try:
        return await service.wrapped(identity, year)
    except ExperienceProfileNotFoundError as exc:
        raise _not_found(exc) from exc
