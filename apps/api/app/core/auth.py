from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, ValidationError

from app.core.config import Settings

_bearer = HTTPBearer(auto_error=False)


class _SupabaseUser(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    id: UUID


@dataclass(frozen=True, slots=True)
class CurrentIdentity:
    auth_user_id: UUID


async def get_current_identity(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> CurrentIdentity:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    settings: Settings = request.app.state.settings
    if not settings.supabase_origin or not settings.supabase_public_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        async with httpx.AsyncClient(
            base_url=settings.supabase_origin,
            timeout=httpx.Timeout(5.0),
            follow_redirects=False,
        ) as client:
            response = await client.get(
                "/auth/v1/user",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {credentials.credentials}",
                    "apikey": settings.supabase_public_key,
                },
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE) from exc

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        user = _SupabaseUser.model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from exc
    return CurrentIdentity(auth_user_id=user.id)
