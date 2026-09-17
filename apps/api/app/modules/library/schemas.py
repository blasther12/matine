from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MovieStatus(StrEnum):
    WATCHLIST = "WATCHLIST"
    WATCHED = "WATCHED"
    DROPPED = "DROPPED"


class LibraryMovieCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: MovieStatus = MovieStatus.WATCHLIST
    rating: float | None = Field(default=None, ge=0.5, le=5, multiple_of=0.5)
    favorite: bool = False


class LibraryMovieUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: MovieStatus | None = None
    rating: float | None = Field(default=None, ge=0.5, le=5, multiple_of=0.5)
    favorite: bool | None = None

    @model_validator(mode="after")
    def require_a_valid_change(self) -> "LibraryMovieUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        if "status" in self.model_fields_set and self.status is None:
            raise ValueError("status cannot be null")
        if "favorite" in self.model_fields_set and self.favorite is None:
            raise ValueError("favorite cannot be null")
        return self


class LibraryMovieResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tmdb_id: int = Field(gt=0, le=2_147_483_647)
    status: MovieStatus
    rating: float | None
    favorite: bool
    created_at: datetime
    updated_at: datetime


class LibraryMovieListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: list[LibraryMovieResponse]
