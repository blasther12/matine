from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentIdentity, get_current_identity
from app.core.database import get_session
from app.modules.users.schemas import ProfileCreate, UserResponse
from app.modules.users.service import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    UserService,
)

router = APIRouter(tags=["account"])


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserService:
    return UserService(session)


@router.get("/me", response_model=UserResponse)
async def me(
    identity: Annotated[CurrentIdentity, Depends(get_current_identity)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    try:
        return await service.me(identity)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.post("/me", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_me(
    payload: ProfileCreate,
    identity: Annotated[CurrentIdentity, Depends(get_current_identity)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    try:
        return await service.create_profile(identity, payload)
    except ProfileAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT) from exc
