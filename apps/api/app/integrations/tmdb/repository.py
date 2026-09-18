from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.tmdb.models import ExternalCache


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class ExternalCacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, provider: str, key: str) -> dict[str, Any] | None:
        entry = await self._session.get(ExternalCache, (provider, key))
        if entry is None:
            return None
        if _as_utc(entry.expires_at) <= datetime.now(UTC):
            await self._session.delete(entry)
            await self._session.flush()
            return None
        return entry.payload

    async def get_many(self, provider: str, keys: list[str]) -> dict[str, dict[str, Any]]:
        if not keys:
            return {}
        rows = (
            await self._session.execute(
                select(ExternalCache).where(
                    ExternalCache.provider == provider,
                    ExternalCache.cache_key.in_(keys),
                    ExternalCache.expires_at > datetime.now(UTC),
                )
            )
        ).scalars()
        return {row.cache_key: row.payload for row in rows}

    async def put(
        self,
        provider: str,
        key: str,
        payload: dict[str, Any],
        ttl: timedelta,
    ) -> None:
        now = datetime.now(UTC)
        await self._session.merge(
            ExternalCache(
                provider=provider,
                cache_key=key,
                payload=payload,
                expires_at=now + ttl,
                created_at=now,
                updated_at=now,
            )
        )

    async def delete(self, provider: str, key: str) -> None:
        entry = await self._session.get(ExternalCache, (provider, key))
        if entry is not None:
            await self._session.delete(entry)
            await self._session.flush()
