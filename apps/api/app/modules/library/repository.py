from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.library.models import Movie, UserMovie


@dataclass(frozen=True, slots=True)
class LibraryRecord:
    tmdb_id: int
    status: str
    rating: Decimal | None
    favorite: bool
    created_at: datetime
    updated_at: datetime


class LibraryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self, user_id: UUID, *, status: str | None = None
    ) -> list[LibraryRecord]:
        statement = (
            select(UserMovie, Movie.tmdb_id)
            .join(Movie, Movie.id == UserMovie.movie_id)
            .where(UserMovie.user_id == user_id)
            .order_by(UserMovie.updated_at.desc(), UserMovie.id.desc())
        )
        if status is not None:
            statement = statement.where(UserMovie.status == status)
        rows = (await self._session.execute(statement)).all()
        return [self._record(user_movie, tmdb_id) for user_movie, tmdb_id in rows]

    async def by_tmdb_id(self, user_id: UUID, tmdb_id: int) -> LibraryRecord | None:
        statement = (
            select(UserMovie, Movie.tmdb_id)
            .join(Movie, Movie.id == UserMovie.movie_id)
            .where(UserMovie.user_id == user_id, Movie.tmdb_id == tmdb_id)
        )
        row = (await self._session.execute(statement)).one_or_none()
        return None if row is None else self._record(row[0], row[1])

    async def upsert(
        self,
        *,
        user_id: UUID,
        tmdb_id: int,
        status: str,
        rating: Decimal | None,
        favorite: bool,
    ) -> LibraryRecord:
        movie_id = (
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
        user_movie = (
            await self._session.execute(
                insert(UserMovie)
                .values(
                    user_id=user_id,
                    movie_id=movie_id,
                    status=status,
                    rating=rating,
                    favorite=favorite,
                )
                .on_conflict_do_update(
                    constraint="uq_user_movies_user_id_movie_id",
                    set_={
                        "status": status,
                        "rating": rating,
                        "favorite": favorite,
                        "updated_at": datetime.now(UTC),
                    },
                )
                .returning(UserMovie)
            )
        ).scalar_one()
        return self._record(user_movie, tmdb_id)

    async def update(
        self,
        *,
        user_id: UUID,
        tmdb_id: int,
        changes: dict[str, object],
    ) -> LibraryRecord | None:
        statement = (
            select(UserMovie)
            .join(Movie, Movie.id == UserMovie.movie_id)
            .where(UserMovie.user_id == user_id, Movie.tmdb_id == tmdb_id)
        )
        user_movie = (await self._session.execute(statement)).scalar_one_or_none()
        if user_movie is None:
            return None
        for field, value in changes.items():
            setattr(user_movie, field, value)
        user_movie.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(user_movie)
        return self._record(user_movie, tmdb_id)

    async def delete(self, user_id: UUID, tmdb_id: int) -> bool:
        movie_id = select(Movie.id).where(Movie.tmdb_id == tmdb_id).scalar_subquery()
        deleted_id = (
            await self._session.execute(
                delete(UserMovie)
                .where(
                    UserMovie.user_id == user_id,
                    UserMovie.movie_id == movie_id,
                )
                .returning(UserMovie.id)
            )
        ).scalar_one_or_none()
        return deleted_id is not None

    @staticmethod
    def _record(user_movie: UserMovie, tmdb_id: int) -> LibraryRecord:
        return LibraryRecord(
            tmdb_id=tmdb_id,
            status=user_movie.status,
            rating=user_movie.rating,
            favorite=user_movie.favorite,
            created_at=user_movie.created_at,
            updated_at=user_movie.updated_at,
        )
