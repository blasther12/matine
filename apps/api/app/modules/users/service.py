from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentIdentity
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import ProfileCreate, UserResponse


class ProfileAlreadyExistsError(Exception):
    """An authenticated identity already owns a profile or username."""


class ProfileNotFoundError(Exception):
    """The authenticated identity has no profile yet."""


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

    async def me(self, identity: CurrentIdentity) -> UserResponse:
        user = await self._users.by_auth_user_id(identity.auth_user_id)
        if user is None:
            raise ProfileNotFoundError
        return UserResponse.model_validate(user)

    async def create_profile(
        self, identity: CurrentIdentity, payload: ProfileCreate
    ) -> UserResponse:
        if await self._users.by_auth_user_id(identity.auth_user_id) is not None:
            raise ProfileAlreadyExistsError
        try:
            user = await self._users.create(
                auth_user_id=identity.auth_user_id,
                username=payload.username,
                display_name=payload.display_name,
                avatar_url=str(payload.avatar_url) if payload.avatar_url is not None else None,
            )
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ProfileAlreadyExistsError from exc
        return UserResponse.model_validate(user)
