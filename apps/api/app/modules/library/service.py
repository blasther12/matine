from decimal import Decimal
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentIdentity
from app.integrations.tmdb.repository import ExternalCacheRepository
from app.modules.movies.schemas import MovieDetailsResponse
from app.modules.library.repository import LibraryRecord, LibraryRepository
from app.modules.library.schemas import (
    LibraryMovieCreate,
    LibraryMovieListResponse,
    LibraryMovieResponse,
    LibraryMovieUpdate,
    MovieStatus,
)
from app.modules.users.repository import UserRepository


class LibraryProfileNotFoundError(Exception):
    """The authenticated identity has no internal profile."""


class LibraryEntryNotFoundError(Exception):
    """No matching entry exists inside the authenticated user's library."""


class LibraryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._library = LibraryRepository(session)
        self._cache = ExternalCacheRepository(session)

    async def list_movies(
        self, identity: CurrentIdentity, *, status: MovieStatus | None = None
    ) -> LibraryMovieListResponse:
        user_id = await self._user_id(identity)
        records = await self._library.list_for_user(
            user_id, status=status.value if status is not None else None
        )
        keys = [self._details_cache_key(record.tmdb_id) for record in records]
        cached = await self._cache.get_many("tmdb", keys)
        items: list[LibraryMovieResponse] = []
        for record in records:
            details = None
            payload = cached.get(self._details_cache_key(record.tmdb_id))
            if payload is not None:
                try:
                    details = MovieDetailsResponse.model_validate(payload)
                except ValidationError:
                    details = None
            items.append(self._response(record, details))
        return LibraryMovieListResponse(items=items)

    async def get_movie(self, identity: CurrentIdentity, tmdb_id: int) -> LibraryMovieResponse:
        user_id = await self._user_id(identity)
        record = await self._library.by_tmdb_id(user_id, tmdb_id)
        if record is None:
            raise LibraryEntryNotFoundError
        return self._response(record)

    async def put_movie(
        self,
        identity: CurrentIdentity,
        tmdb_id: int,
        payload: LibraryMovieCreate,
    ) -> LibraryMovieResponse:
        user_id = await self._user_id(identity)
        record = await self._library.upsert(
            user_id=user_id,
            tmdb_id=tmdb_id,
            status=payload.status.value,
            rating=self._decimal(payload.rating),
            favorite=payload.favorite,
        )
        await self._session.commit()
        return self._response(record)

    async def patch_movie(
        self,
        identity: CurrentIdentity,
        tmdb_id: int,
        payload: LibraryMovieUpdate,
    ) -> LibraryMovieResponse:
        user_id = await self._user_id(identity)
        changes: dict[str, object] = {}
        if "status" in payload.model_fields_set and payload.status is not None:
            changes["status"] = payload.status.value
        if "rating" in payload.model_fields_set:
            changes["rating"] = self._decimal(payload.rating)
        if "favorite" in payload.model_fields_set and payload.favorite is not None:
            changes["favorite"] = payload.favorite
        record = await self._library.update(user_id=user_id, tmdb_id=tmdb_id, changes=changes)
        if record is None:
            raise LibraryEntryNotFoundError
        await self._session.commit()
        return self._response(record)

    async def delete_movie(self, identity: CurrentIdentity, tmdb_id: int) -> None:
        user_id = await self._user_id(identity)
        if not await self._library.delete(user_id, tmdb_id):
            raise LibraryEntryNotFoundError
        await self._session.commit()

    async def _user_id(self, identity: CurrentIdentity) -> UUID:
        user = await self._users.by_auth_user_id(identity.auth_user_id)
        if user is None:
            raise LibraryProfileNotFoundError
        return user.id

    @staticmethod
    def _decimal(value: float | None) -> Decimal | None:
        return None if value is None else Decimal(str(value))

    @staticmethod
    def _details_cache_key(tmdb_id: int) -> str:
        return f"movie:details:v1:pt-BR:{tmdb_id}"

    @staticmethod
    def _response(
        record: LibraryRecord,
        details: MovieDetailsResponse | None = None,
    ) -> LibraryMovieResponse:
        return LibraryMovieResponse(
            tmdb_id=record.tmdb_id,
            status=MovieStatus(record.status),
            rating=float(record.rating) if record.rating is not None else None,
            favorite=record.favorite,
            title=details.title if details is not None else None,
            year=details.year if details is not None else None,
            poster_path=details.poster_path if details is not None else None,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
