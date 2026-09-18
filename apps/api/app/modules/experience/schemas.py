from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewVisibility(StrEnum):
    PRIVATE = "PRIVATE"
    FOLLOWERS = "FOLLOWERS"
    PUBLIC = "PUBLIC"


class ListVisibility(StrEnum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"


class DiaryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tmdb_id: int = Field(gt=0, le=2_147_483_647)
    watched_at: date
    rewatch: bool = False
    notes: str | None = Field(default=None, max_length=2000)


class DiaryEntryResponse(DiaryCreate):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    title: str | None = None
    poster_path: str | None = None
    created_at: datetime


class ReviewUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tmdb_id: int = Field(gt=0, le=2_147_483_647)
    body: str = Field(min_length=1, max_length=5000)
    spoiler: bool = False
    visibility: ReviewVisibility = ReviewVisibility.PRIVATE


class ReviewResponse(ReviewUpsert):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    username: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class MovieListCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    visibility: ListVisibility = ListVisibility.PRIVATE


class MovieListItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tmdb_id: int = Field(gt=0, le=2_147_483_647)
    position: int = Field(ge=0, le=9999)
    note: str | None = Field(default=None, max_length=500)


class MovieListItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tmdb_id: int
    position: int
    note: str | None
    title: str | None = None
    poster_path: str | None = None


class MovieListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    name: str
    description: str | None
    visibility: ListVisibility
    items: list[MovieListItemResponse]
    created_at: datetime
    updated_at: datetime


class FollowCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.lower()


class FeedItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    username: str
    tmdb_id: int
    title: str | None
    body: str
    spoiler: bool
    created_at: datetime


class StreamingPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    providers: list[str] = Field(max_length=20)

    @field_validator("providers")
    @classmethod
    def normalize_providers(cls, values: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for raw in values:
            value = raw.strip()[:120]
            key = value.casefold()
            if value and key not in seen:
                unique.append(value)
                seen.add(key)
        return unique


class CircleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)


class CircleMemberCreate(FollowCreate):
    pass


class CircleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    name: str
    role: str
    member_count: int
    created_at: datetime


class MatchItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tmdb_id: int
    title: str | None
    poster_path: str | None
    interested_members: int
    member_count: int
    score: float
    reason: str


class MovieNightCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=120)


class MovieNightCandidateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tmdb_id: int = Field(gt=0, le=2_147_483_647)


class MovieNightVoteCreate(MovieNightCandidateCreate):
    pass


class MovieNightResultItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tmdb_id: int
    title: str | None
    votes: int


class MovieNightResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    circle_id: UUID
    title: str
    status: str
    results: list[MovieNightResultItem]
    created_at: datetime


class RecommendationItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tmdb_id: int
    title: str | None
    poster_path: str | None
    score: float
    reasons: list[str]


class StatsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    library_total: int
    watchlist_total: int
    watched_total: int
    dropped_total: int
    favorite_total: int
    diary_total: int
    review_total: int
    list_total: int
    average_rating: float | None


class WrappedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    year: int
    watches: int
    distinct_movies: int
    rewatches: int
    reviews: int
    top_movie_tmdb_id: int | None
    top_movie_title: str | None
