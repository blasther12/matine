from datetime import date
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentIdentity
from app.integrations.tmdb.repository import ExternalCacheRepository
from app.modules.experience.models import MovieList
from app.modules.experience.repository import (
    DiaryRecord,
    ExperienceRepository,
    ListItemRecord,
    ReviewRecord,
)
from app.modules.experience.schemas import (
    CircleCreate,
    CircleMemberCreate,
    CircleResponse,
    DiaryCreate,
    DiaryEntryResponse,
    FeedItem,
    FollowCreate,
    ListVisibility,
    MatchItem,
    MovieListCreate,
    MovieListItemCreate,
    MovieListItemResponse,
    MovieListResponse,
    MovieNightCandidateCreate,
    MovieNightCreate,
    MovieNightResponse,
    MovieNightResultItem,
    MovieNightVoteCreate,
    RecommendationItem,
    ReviewResponse,
    ReviewUpsert,
    StatsResponse,
    StreamingPreferences,
    WrappedResponse,
)
from app.modules.movies.schemas import MovieDetailsResponse
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


class ExperienceProfileNotFoundError(Exception):
    pass


class ExperienceNotFoundError(Exception):
    pass


class ExperienceForbiddenError(Exception):
    pass


class ExperienceService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._repo = ExperienceRepository(session)
        self._cache = ExternalCacheRepository(session)

    async def _user(self, identity: CurrentIdentity) -> User:
        user = await self._users.by_auth_user_id(identity.auth_user_id)
        if user is None:
            raise ExperienceProfileNotFoundError
        return user

    @staticmethod
    def _cache_key(tmdb_id: int) -> str:
        return f"movie:details:v1:pt-BR:{tmdb_id}"

    async def _metadata(self, tmdb_ids: list[int]) -> dict[int, MovieDetailsResponse]:
        keys = [self._cache_key(value) for value in tmdb_ids]
        cached = await self._cache.get_many("tmdb", keys)
        result: dict[int, MovieDetailsResponse] = {}
        for tmdb_id in tmdb_ids:
            payload = cached.get(self._cache_key(tmdb_id))
            if payload is None:
                continue
            try:
                result[tmdb_id] = MovieDetailsResponse.model_validate(payload)
            except ValidationError:
                continue
        return result

    async def diary(self, identity: CurrentIdentity) -> list[DiaryEntryResponse]:
        user = await self._user(identity)
        records = await self._repo.list_diary(user.id)
        metadata = await self._metadata([record.tmdb_id for record in records])
        return [self._diary_response(record, metadata.get(record.tmdb_id)) for record in records]

    async def add_diary(
        self, identity: CurrentIdentity, payload: DiaryCreate
    ) -> DiaryEntryResponse:
        user = await self._user(identity)
        record = await self._repo.add_diary(
            user.id,
            tmdb_id=payload.tmdb_id,
            watched_at=payload.watched_at,
            rewatch=payload.rewatch,
            notes=payload.notes,
        )
        await self._session.commit()
        metadata = await self._metadata([payload.tmdb_id])
        return self._diary_response(record, metadata.get(payload.tmdb_id))

    async def reviews(self, identity: CurrentIdentity) -> list[ReviewResponse]:
        user = await self._user(identity)
        records = await self._repo.list_reviews(user.id, user.username)
        metadata = await self._metadata([record.tmdb_id for record in records])
        return [self._review_response(record, metadata.get(record.tmdb_id)) for record in records]

    async def save_review(
        self, identity: CurrentIdentity, payload: ReviewUpsert
    ) -> ReviewResponse:
        user = await self._user(identity)
        record = await self._repo.upsert_review(
            user.id,
            user.username,
            tmdb_id=payload.tmdb_id,
            body=payload.body,
            spoiler=payload.spoiler,
            visibility=payload.visibility.value,
        )
        await self._session.commit()
        metadata = await self._metadata([payload.tmdb_id])
        return self._review_response(record, metadata.get(payload.tmdb_id))

    async def feed(self, identity: CurrentIdentity) -> list[FeedItem]:
        user = await self._user(identity)
        records = await self._repo.feed(user.id)
        metadata = await self._metadata([record.tmdb_id for record in records])
        return [
            FeedItem(
                username=record.username,
                tmdb_id=record.tmdb_id,
                title=metadata.get(record.tmdb_id).title
                if record.tmdb_id in metadata
                else None,
                body=record.review.body,
                spoiler=record.review.spoiler,
                created_at=record.review.created_at,
            )
            for record in records
        ]

    async def follow(self, identity: CurrentIdentity, payload: FollowCreate) -> None:
        user = await self._user(identity)
        if not await self._repo.follow(user.id, payload.username):
            raise ExperienceNotFoundError
        await self._session.commit()

    async def lists(self, identity: CurrentIdentity) -> list[MovieListResponse]:
        user = await self._user(identity)
        records = await self._repo.lists_for_user(user.id)
        ids = [item.tmdb_id for _, items in records for item in items]
        metadata = await self._metadata(ids)
        return [
            self._list_response(value, items, metadata)
            for value, items in records
        ]

    async def create_list(
        self, identity: CurrentIdentity, payload: MovieListCreate
    ) -> MovieListResponse:
        user = await self._user(identity)
        value = await self._repo.create_list(
            user.id,
            name=payload.name,
            description=payload.description,
            visibility=payload.visibility.value,
        )
        await self._session.commit()
        return MovieListResponse(
            id=value.id,
            name=value.name,
            description=value.description,
            visibility=ListVisibility(value.visibility),
            items=[],
            created_at=value.created_at,
            updated_at=value.updated_at,
        )

    async def add_list_item(
        self,
        identity: CurrentIdentity,
        list_id: UUID,
        payload: MovieListItemCreate,
    ) -> None:
        user = await self._user(identity)
        if not await self._repo.add_list_item(
            user.id,
            list_id,
            tmdb_id=payload.tmdb_id,
            position=payload.position,
            note=payload.note,
        ):
            raise ExperienceNotFoundError
        await self._session.commit()

    async def streaming(self, identity: CurrentIdentity) -> StreamingPreferences:
        user = await self._user(identity)
        return StreamingPreferences(providers=await self._repo.streaming(user.id))

    async def save_streaming(
        self, identity: CurrentIdentity, payload: StreamingPreferences
    ) -> StreamingPreferences:
        user = await self._user(identity)
        values = await self._repo.replace_streaming(user.id, payload.providers)
        await self._session.commit()
        return StreamingPreferences(providers=values)

    async def circles(self, identity: CurrentIdentity) -> list[CircleResponse]:
        user = await self._user(identity)
        return [
            CircleResponse(
                id=circle.id,
                name=circle.name,
                role=role,
                member_count=count,
                created_at=circle.created_at,
            )
            for circle, role, count in await self._repo.circles_for_user(user.id)
        ]

    async def create_circle(
        self, identity: CurrentIdentity, payload: CircleCreate
    ) -> CircleResponse:
        user = await self._user(identity)
        circle = await self._repo.create_circle(user.id, payload.name)
        await self._session.commit()
        return CircleResponse(
            id=circle.id,
            name=circle.name,
            role="OWNER",
            member_count=1,
            created_at=circle.created_at,
        )

    async def add_circle_member(
        self,
        identity: CurrentIdentity,
        circle_id: UUID,
        payload: CircleMemberCreate,
    ) -> None:
        user = await self._user(identity)
        if not await self._repo.add_circle_member(circle_id, user.id, payload.username):
            raise ExperienceForbiddenError
        await self._session.commit()

    async def match(
        self, identity: CurrentIdentity, circle_id: UUID
    ) -> list[MatchItem]:
        user = await self._user(identity)
        if await self._repo.circle_role(circle_id, user.id) is None:
            raise ExperienceForbiddenError
        member_count, candidates = await self._repo.match_candidates(circle_id)
        metadata = await self._metadata([tmdb_id for tmdb_id, _ in candidates])
        return [
            MatchItem(
                tmdb_id=tmdb_id,
                title=metadata.get(tmdb_id).title if tmdb_id in metadata else None,
                poster_path=(
                    metadata.get(tmdb_id).poster_path if tmdb_id in metadata else None
                ),
                interested_members=interested,
                member_count=member_count,
                score=round(interested / member_count, 3) if member_count else 0,
                reason=f"{interested} de {member_count} membros querem assistir",
            )
            for tmdb_id, interested in candidates
        ]

    async def create_night(
        self,
        identity: CurrentIdentity,
        circle_id: UUID,
        payload: MovieNightCreate,
    ) -> MovieNightResponse:
        user = await self._user(identity)
        night = await self._repo.create_night(circle_id, user.id, payload.title)
        if night is None:
            raise ExperienceForbiddenError
        await self._session.commit()
        return MovieNightResponse(
            id=night.id,
            circle_id=night.circle_id,
            title=night.title,
            status=night.status,
            results=[],
            created_at=night.created_at,
        )

    async def add_candidate(
        self,
        identity: CurrentIdentity,
        night_id: UUID,
        payload: MovieNightCandidateCreate,
    ) -> None:
        user = await self._user(identity)
        if not await self._repo.add_candidate(night_id, user.id, payload.tmdb_id):
            raise ExperienceForbiddenError
        await self._session.commit()

    async def vote(
        self,
        identity: CurrentIdentity,
        night_id: UUID,
        payload: MovieNightVoteCreate,
    ) -> None:
        user = await self._user(identity)
        if not await self._repo.vote(night_id, user.id, payload.tmdb_id):
            raise ExperienceForbiddenError
        await self._session.commit()

    async def night(
        self, identity: CurrentIdentity, night_id: UUID
    ) -> MovieNightResponse:
        user = await self._user(identity)
        night, results = await self._repo.night_results(night_id, user.id)
        if night is None:
            raise ExperienceNotFoundError
        metadata = await self._metadata([tmdb_id for tmdb_id, _ in results])
        return MovieNightResponse(
            id=night.id,
            circle_id=night.circle_id,
            title=night.title,
            status=night.status,
            results=[
                MovieNightResultItem(
                    tmdb_id=tmdb_id,
                    title=metadata.get(tmdb_id).title
                    if tmdb_id in metadata
                    else None,
                    votes=votes,
                )
                for tmdb_id, votes in results
            ],
            created_at=night.created_at,
        )

    async def recommendations(
        self, identity: CurrentIdentity
    ) -> list[RecommendationItem]:
        user = await self._user(identity)
        rows = await self._repo.library_rows(user.id)
        metadata = await self._metadata([tmdb_id for _, tmdb_id in rows])

        genre_weights: dict[int, float] = {}
        for entry, tmdb_id in rows:
            details = metadata.get(tmdb_id)
            if entry.status != "WATCHED" or details is None:
                continue
            weight = float(entry.rating or 0) + (2.0 if entry.favorite else 0.0)
            for genre in details.genres:
                genre_weights[genre.tmdb_id] = genre_weights.get(genre.tmdb_id, 0.0) + weight

        ranked: list[RecommendationItem] = []
        for entry, tmdb_id in rows:
            if entry.status != "WATCHLIST":
                continue
            details = metadata.get(tmdb_id)
            if details is None:
                continue
            affinity = sum(genre_weights.get(genre.tmdb_id, 0.0) for genre in details.genres)
            score = details.vote_average + min(affinity / 10.0, 5.0)
            reasons = [f"TMDB {details.vote_average:.1f}/10"]
            matched = [
                genre.name
                for genre in details.genres
                if genre_weights.get(genre.tmdb_id, 0.0) > 0
            ][:2]
            if matched:
                reasons.append("combina com " + " e ".join(matched))
            ranked.append(
                RecommendationItem(
                    tmdb_id=tmdb_id,
                    title=details.title,
                    poster_path=details.poster_path,
                    score=round(score, 2),
                    reasons=reasons,
                )
            )
        return sorted(ranked, key=lambda item: item.score, reverse=True)[:20]

    async def stats(self, identity: CurrentIdentity) -> StatsResponse:
        user = await self._user(identity)
        return StatsResponse.model_validate(await self._repo.stats(user.id))

    async def wrapped(self, identity: CurrentIdentity, year: int) -> WrappedResponse:
        user = await self._user(identity)
        values = await self._repo.wrapped(user.id, year)
        top_id = values["top_movie_tmdb_id"]
        metadata = await self._metadata([int(top_id)]) if top_id is not None else {}
        return WrappedResponse(
            year=year,
            watches=int(values["watches"] or 0),
            distinct_movies=int(values["distinct_movies"] or 0),
            rewatches=int(values["rewatches"] or 0),
            reviews=int(values["reviews"] or 0),
            top_movie_tmdb_id=int(top_id) if top_id is not None else None,
            top_movie_title=(
                metadata[int(top_id)].title
                if top_id is not None and int(top_id) in metadata
                else None
            ),
        )

    @staticmethod
    def _diary_response(
        record: DiaryRecord, details: MovieDetailsResponse | None
    ) -> DiaryEntryResponse:
        return DiaryEntryResponse(
            id=record.entry.id,
            tmdb_id=record.tmdb_id,
            watched_at=record.entry.watched_at,
            rewatch=record.entry.rewatch,
            notes=record.entry.notes,
            title=details.title if details else None,
            poster_path=details.poster_path if details else None,
            created_at=record.entry.created_at,
        )

    @staticmethod
    def _review_response(
        record: ReviewRecord, details: MovieDetailsResponse | None
    ) -> ReviewResponse:
        return ReviewResponse(
            id=record.review.id,
            username=record.username,
            tmdb_id=record.tmdb_id,
            title=details.title if details else None,
            body=record.review.body,
            spoiler=record.review.spoiler,
            visibility=record.review.visibility,
            created_at=record.review.created_at,
            updated_at=record.review.updated_at,
        )

    @staticmethod
    def _list_response(
        value: MovieList,
        items: list[ListItemRecord],
        metadata: dict[int, MovieDetailsResponse],
    ) -> MovieListResponse:
        return MovieListResponse(
            id=value.id,
            name=value.name,
            description=value.description,
            visibility=value.visibility,
            items=[
                MovieListItemResponse(
                    tmdb_id=item.tmdb_id,
                    position=item.item.position,
                    note=item.item.note,
                    title=metadata[item.tmdb_id].title
                    if item.tmdb_id in metadata
                    else None,
                    poster_path=metadata[item.tmdb_id].poster_path
                    if item.tmdb_id in metadata
                    else None,
                )
                for item in items
            ],
            created_at=value.created_at,
            updated_at=value.updated_at,
        )
