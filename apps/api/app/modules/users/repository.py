from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def by_auth_user_id(self, auth_user_id: UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.auth_user_id == auth_user_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        auth_user_id: UUID,
        username: str,
        display_name: str,
        avatar_url: str | None,
    ) -> User:
        user = User(
            auth_user_id=auth_user_id,
            username=username,
            display_name=display_name,
            avatar_url=avatar_url,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user
