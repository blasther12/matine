from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.experience.models import (
    Circle,
    CircleMember,
    Follow,
    MovieList,
    MovieListItem,
    MovieNight,
    MovieNightCandidate,
    MovieNightVote,
    Review,
    StreamingPreference,
    WatchEntry,
)
from app.modules.library.models import Movie, UserMovie
from app.modules.users.models import User


@dataclass(frozen=True, slots=True)
class DiaryRecord:
    entry: WatchEntry
    tmdb_id: int


@dataclass(frozen=True, slots=True)
class ReviewRecord:
    review: Review
    tmdb_id: int
    username: str


@dataclass(frozen=True, slots=True)
class ListItemRecord:
    item: MovieListItem
    tmdb_id: int


class ExperienceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def user_by_username(self, username: str) -> User | None:
        result = await self._session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def ensure_movie(self, tmdb_id: int) -> UUID:
        return (
            await self._session.execute(
                insert(Movie)
                .values(tmdb_id=tmdb_id)
                .on_conflict_do_update(
                    index_elements=[Movie.tmdb_id],
                    set_={"tmdb_id": tmdb_id},
                )
                .returning(Movie.id)
            )
        ).scalar_one()

    async def list_diary(self, user_id: UUID) -> list[DiaryRecord]:
        rows = (
            await self._session.execute(
                select(WatchEntry, Movie.tmdb_id)
                .join(Movie, Movie.id == WatchEntry.movie_id)
                .where(WatchEntry.user_id == user_id)
                .order_by(WatchEntry.watched_at.desc(), WatchEntry.created_at.desc())
                .limit(250)
            )
        ).all()
        return [DiaryRecord(entry=row[0], tmdb_id=row[1]) for row in rows]

    async def add_diary(
        self,
        user_id: UUID,
        *,
        tmdb_id: int,
        watched_at: date,
        rewatch: bool,
        notes: str | None,
    ) -> DiaryRecord:
        movie_id = await self.ensure_movie(tmdb_id)
        entry = WatchEntry(
            user_id=user_id,
            movie_id=movie_id,
            watched_at=watched_at,
            rewatch=rewatch,
            notes=notes,
        )
        self._session.add(entry)
        await self._session.flush()
        await self._session.refresh(entry)
        return DiaryRecord(entry=entry, tmdb_id=tmdb_id)

    async def list_reviews(self, user_id: UUID, username: str) -> list[ReviewRecord]:
        rows = (
            await self._session.execute(
                select(Review, Movie.tmdb_id)
                .join(Movie, Movie.id == Review.movie_id)
                .where(Review.user_id == user_id)
                .order_by(Review.updated_at.desc())
                .limit(200)
            )
        ).all()
        return [ReviewRecord(review=row[0], tmdb_id=row[1], username=username) for row in rows]

    async def upsert_review(
        self,
        user_id: UUID,
        username: str,
        *,
        tmdb_id: int,
        body: str,
        spoiler: bool,
        visibility: str,
    ) -> ReviewRecord:
        movie_id = await self.ensure_movie(tmdb_id)
        review = (
            await self._session.execute(
                insert(Review)
                .values(
                    user_id=user_id,
                    movie_id=movie_id,
                    body=body,
                    spoiler=spoiler,
                    visibility=visibility,
                )
                .on_conflict_do_update(
                    constraint="uq_reviews_user_movie",
                    set_={
                        "body": body,
                        "spoiler": spoiler,
                        "visibility": visibility,
                        "updated_at": datetime.now(UTC),
                    },
                )
                .returning(Review)
            )
        ).scalar_one()
        return ReviewRecord(review=review, tmdb_id=tmdb_id, username=username)

    async def feed(self, user_id: UUID) -> list[ReviewRecord]:
        followed = select(Follow.followee_id).where(Follow.follower_id == user_id)
        rows = (
            await self._session.execute(
                select(Review, Movie.tmdb_id, User.username)
                .join(Movie, Movie.id == Review.movie_id)
                .join(User, User.id == Review.user_id)
                .where(
                    (Review.visibility == "PUBLIC")
                    | (
                        (Review.visibility == "FOLLOWERS")
                        & Review.user_id.in_(followed)
                    )
                )
                .order_by(Review.updated_at.desc())
                .limit(100)
            )
        ).all()
        return [
            ReviewRecord(review=row[0], tmdb_id=row[1], username=row[2])
            for row in rows
        ]

    async def create_list(
        self,
        user_id: UUID,
        *,
        name: str,
        description: str | None,
        visibility: str,
    ) -> MovieList:
        value = MovieList(
            user_id=user_id,
            name=name,
            description=description,
            visibility=visibility,
        )
        self._session.add(value)
        await self._session.flush()
        await self._session.refresh(value)
        return value

    async def lists_for_user(
        self, user_id: UUID
    ) -> list[tuple[MovieList, list[ListItemRecord]]]:
        lists = (
            await self._session.execute(
                select(MovieList)
                .where(MovieList.user_id == user_id)
                .order_by(MovieList.updated_at.desc())
            )
        ).scalars().all()
        if not lists:
            return []
        ids = [value.id for value in lists]
        rows = (
            await self._session.execute(
                select(MovieListItem, Movie.tmdb_id)
                .join(Movie, Movie.id == MovieListItem.movie_id)
                .where(MovieListItem.list_id.in_(ids))
                .order_by(MovieListItem.list_id, MovieListItem.position)
            )
        ).all()
        grouped: dict[UUID, list[ListItemRecord]] = {value.id: [] for value in lists}
        for item, tmdb_id in rows:
            grouped[item.list_id].append(ListItemRecord(item=item, tmdb_id=tmdb_id))
        return [(value, grouped[value.id]) for value in lists]

    async def add_list_item(
        self,
        user_id: UUID,
        list_id: UUID,
        *,
        tmdb_id: int,
        position: int,
        note: str | None,
    ) -> bool:
        owned = (
            await self._session.execute(
                select(MovieList.id).where(
                    MovieList.id == list_id,
                    MovieList.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        if owned is None:
            return False
        movie_id = await self.ensure_movie(tmdb_id)
        await self._session.execute(
            insert(MovieListItem)
            .values(
                list_id=list_id,
                movie_id=movie_id,
                position=position,
                note=note,
            )
            .on_conflict_do_update(
                constraint="uq_movie_list_items_list_movie",
                set_={"position": position, "note": note},
            )
        )
        return True

    async def follow(self, follower_id: UUID, username: str) -> bool:
        target = await self.user_by_username(username)
        if target is None or target.id == follower_id:
            return False
        await self._session.execute(
            insert(Follow)
            .values(follower_id=follower_id, followee_id=target.id)
            .on_conflict_do_nothing()
        )
        return True

    async def streaming(self, user_id: UUID) -> list[str]:
        return list(
            (
                await self._session.execute(
                    select(StreamingPreference.provider_name)
                    .where(StreamingPreference.user_id == user_id)
                    .order_by(StreamingPreference.provider_name)
                )
            ).scalars()
        )

    async def replace_streaming(self, user_id: UUID, providers: list[str]) -> list[str]:
        await self._session.execute(
            delete(StreamingPreference).where(StreamingPreference.user_id == user_id)
        )
        for provider in providers:
            self._session.add(
                StreamingPreference(user_id=user_id, provider_name=provider)
            )
        await self._session.flush()
        return providers

    async def create_circle(self, user_id: UUID, name: str) -> Circle:
        circle = Circle(owner_user_id=user_id, name=name)
        self._session.add(circle)
        await self._session.flush()
        self._session.add(
            CircleMember(circle_id=circle.id, user_id=user_id, role="OWNER")
        )
        await self._session.flush()
        await self._session.refresh(circle)
        return circle

    async def circles_for_user(
        self, user_id: UUID
    ) -> list[tuple[Circle, str, int]]:
        member_count = (
            select(
                CircleMember.circle_id,
                func.count(CircleMember.user_id).label("member_count"),
            )
            .group_by(CircleMember.circle_id)
            .subquery()
        )
        rows = (
            await self._session.execute(
                select(Circle, CircleMember.role, member_count.c.member_count)
                .join(
                    CircleMember,
                    (CircleMember.circle_id == Circle.id)
                    & (CircleMember.user_id == user_id),
                )
                .join(member_count, member_count.c.circle_id == Circle.id)
                .order_by(Circle.created_at.desc())
            )
        ).all()
        return [(row[0], row[1], int(row[2])) for row in rows]

    async def circle_role(self, circle_id: UUID, user_id: UUID) -> str | None:
        return (
            await self._session.execute(
                select(CircleMember.role).where(
                    CircleMember.circle_id == circle_id,
                    CircleMember.user_id == user_id,
                )
            )
        ).scalar_one_or_none()

    async def add_circle_member(
        self, circle_id: UUID, owner_id: UUID, username: str
    ) -> bool:
        if await self.circle_role(circle_id, owner_id) != "OWNER":
            return False
        target = await self.user_by_username(username)
        if target is None:
            return False
        await self._session.execute(
            insert(CircleMember)
            .values(circle_id=circle_id, user_id=target.id, role="MEMBER")
            .on_conflict_do_nothing()
        )
        return True

    async def circle_members(self, circle_id: UUID) -> list[UUID]:
        return list(
            (
                await self._session.execute(
                    select(CircleMember.user_id).where(
                        CircleMember.circle_id == circle_id
                    )
                )
            ).scalars()
        )

    async def match_candidates(
        self, circle_id: UUID
    ) -> tuple[int, list[tuple[int, int]]]:
        members = await self.circle_members(circle_id)
        if not members:
            return 0, []
        rows = (
            await self._session.execute(
                select(
                    Movie.tmdb_id,
                    func.count(func.distinct(UserMovie.user_id)).label("interested"),
                )
                .join(UserMovie, UserMovie.movie_id == Movie.id)
                .where(
                    UserMovie.user_id.in_(members),
                    UserMovie.status == "WATCHLIST",
                )
                .group_by(Movie.tmdb_id)
                .order_by(func.count(func.distinct(UserMovie.user_id)).desc())
                .limit(50)
            )
        ).all()
        return len(members), [(int(row[0]), int(row[1])) for row in rows]

    async def create_night(
        self, circle_id: UUID, user_id: UUID, title: str
    ) -> MovieNight | None:
        if await self.circle_role(circle_id, user_id) is None:
            return None
        night = MovieNight(
            circle_id=circle_id,
            created_by_user_id=user_id,
            title=title,
        )
        self._session.add(night)
        await self._session.flush()
        await self._session.refresh(night)
        return night

    async def night_for_member(
        self, night_id: UUID, user_id: UUID
    ) -> MovieNight | None:
        return (
            await self._session.execute(
                select(MovieNight)
                .join(
                    CircleMember,
                    (CircleMember.circle_id == MovieNight.circle_id)
                    & (CircleMember.user_id == user_id),
                )
                .where(MovieNight.id == night_id)
            )
        ).scalar_one_or_none()

    async def add_candidate(
        self, night_id: UUID, user_id: UUID, tmdb_id: int
    ) -> bool:
        night = await self.night_for_member(night_id, user_id)
        if night is None or night.status != "OPEN":
            return False
        movie_id = await self.ensure_movie(tmdb_id)
        await self._session.execute(
            insert(MovieNightCandidate)
            .values(
                night_id=night_id,
                movie_id=movie_id,
                added_by_user_id=user_id,
            )
            .on_conflict_do_nothing()
        )
        return True

    async def vote(self, night_id: UUID, user_id: UUID, tmdb_id: int) -> bool:
        night = await self.night_for_member(night_id, user_id)
        if night is None or night.status != "OPEN":
            return False
        movie_id = (
            await self._session.execute(
                select(Movie.id)
                .join(
                    MovieNightCandidate,
                    MovieNightCandidate.movie_id == Movie.id,
                )
                .where(
                    MovieNightCandidate.night_id == night_id,
                    Movie.tmdb_id == tmdb_id,
                )
            )
        ).scalar_one_or_none()
        if movie_id is None:
            return False
        await self._session.execute(
            insert(MovieNightVote)
            .values(night_id=night_id, user_id=user_id, movie_id=movie_id)
            .on_conflict_do_update(
                constraint="uq_movie_night_votes_night_user",
                set_={"movie_id": movie_id, "created_at": datetime.now(UTC)},
            )
        )
        return True

    async def night_results(
        self, night_id: UUID, user_id: UUID
    ) -> tuple[MovieNight | None, list[tuple[int, int]]]:
        night = await self.night_for_member(night_id, user_id)
        if night is None:
            return None, []
        rows = (
            await self._session.execute(
                select(
                    Movie.tmdb_id,
                    func.count(MovieNightVote.id).label("votes"),
                )
                .join(
                    MovieNightCandidate,
                    MovieNightCandidate.movie_id == Movie.id,
                )
                .outerjoin(
                    MovieNightVote,
                    (MovieNightVote.night_id == night_id)
                    & (MovieNightVote.movie_id == Movie.id),
                )
                .where(MovieNightCandidate.night_id == night_id)
                .group_by(Movie.tmdb_id)
                .order_by(func.count(MovieNightVote.id).desc(), Movie.tmdb_id)
            )
        ).all()
        return night, [(int(row[0]), int(row[1])) for row in rows]

    async def library_rows(self, user_id: UUID) -> list[tuple[UserMovie, int]]:
        return list(
            (
                await self._session.execute(
                    select(UserMovie, Movie.tmdb_id)
                    .join(Movie, Movie.id == UserMovie.movie_id)
                    .where(UserMovie.user_id == user_id)
                    .order_by(UserMovie.updated_at.desc())
                )
            ).all()
        )

    async def stats(self, user_id: UUID) -> dict[str, int | float | None]:
        statuses = dict(
            (
                await self._session.execute(
                    select(UserMovie.status, func.count(UserMovie.id))
                    .where(UserMovie.user_id == user_id)
                    .group_by(UserMovie.status)
                )
            ).all()
        )
        aggregate = (
            await self._session.execute(
                select(
                    func.count(UserMovie.id),
                    func.count(UserMovie.id).filter(UserMovie.favorite.is_(True)),
                    func.avg(UserMovie.rating),
                ).where(UserMovie.user_id == user_id)
            )
        ).one()
        diary_total = (
            await self._session.execute(
                select(func.count(WatchEntry.id)).where(WatchEntry.user_id == user_id)
            )
        ).scalar_one()
        review_total = (
            await self._session.execute(
                select(func.count(Review.id)).where(Review.user_id == user_id)
            )
        ).scalar_one()
        list_total = (
            await self._session.execute(
                select(func.count(MovieList.id)).where(MovieList.user_id == user_id)
            )
        ).scalar_one()
        return {
            "library_total": int(aggregate[0]),
            "watchlist_total": int(statuses.get("WATCHLIST", 0)),
            "watched_total": int(statuses.get("WATCHED", 0)),
            "dropped_total": int(statuses.get("DROPPED", 0)),
            "favorite_total": int(aggregate[1]),
            "diary_total": int(diary_total),
            "review_total": int(review_total),
            "list_total": int(list_total),
            "average_rating": (
                round(float(aggregate[2]), 2) if aggregate[2] is not None else None
            ),
        }

    async def wrapped(
        self, user_id: UUID, year: int
    ) -> dict[str, int | None]:
        start = date(year, 1, 1)
        end = date(year + 1, 1, 1)
        diary = (
            await self._session.execute(
                select(
                    func.count(WatchEntry.id),
                    func.count(func.distinct(WatchEntry.movie_id)),
                    func.count(WatchEntry.id).filter(WatchEntry.rewatch.is_(True)),
                ).where(
                    WatchEntry.user_id == user_id,
                    WatchEntry.watched_at >= start,
                    WatchEntry.watched_at < end,
                )
            )
        ).one()
        reviews = (
            await self._session.execute(
                select(func.count(Review.id)).where(
                    Review.user_id == user_id,
                    Review.created_at >= datetime(year, 1, 1, tzinfo=UTC),
                    Review.created_at < datetime(year + 1, 1, 1, tzinfo=UTC),
                )
            )
        ).scalar_one()
        top_tmdb = (
            await self._session.execute(
                select(Movie.tmdb_id)
                .join(UserMovie, UserMovie.movie_id == Movie.id)
                .where(
                    UserMovie.user_id == user_id,
                    UserMovie.rating.is_not(None),
                )
                .order_by(UserMovie.rating.desc(), UserMovie.updated_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return {
            "watches": int(diary[0]),
            "distinct_movies": int(diary[1]),
            "rewatches": int(diary[2]),
            "reviews": int(reviews),
            "top_movie_tmdb_id": int(top_tmdb) if top_tmdb is not None else None,
        }
