from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MAX_TMDB_ID = 2_147_483_647
_TMDB_NOTICE = "This product uses the TMDB API but is not endorsed or certified by TMDB."
_JUSTWATCH_NOTICE = "Streaming availability data provided by JustWatch."
_IMAGE_PATH_PATTERN = r"^/[A-Za-z0-9._/-]+$"


class PublicModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TMDBAttribution(PublicModel):
    source: Literal["TMDB"] = "TMDB"
    notice: str = _TMDB_NOTICE


class JustWatchAttribution(PublicModel):
    source: Literal["JustWatch"] = "JustWatch"
    notice: str = _JUSTWATCH_NOTICE


class MovieSearchItem(PublicModel):
    tmdb_id: int = Field(ge=1, le=MAX_TMDB_ID)
    title: str = Field(min_length=1, max_length=500)
    original_title: str = Field(min_length=1, max_length=500)
    overview: str = Field(max_length=10_000)
    release_date: date | None
    year: int | None = Field(default=None, ge=1800, le=3000)
    poster_path: str | None = Field(default=None, max_length=255, pattern=_IMAGE_PATH_PATTERN)
    vote_average: float = Field(ge=0, le=10)


class MovieSearchResponse(PublicModel):
    page: int = Field(ge=1, le=500)
    total_pages: int = Field(ge=0, le=500)
    total_results: int = Field(ge=0)
    results: tuple[MovieSearchItem, ...]
    attribution: TMDBAttribution = Field(default_factory=TMDBAttribution)


class Genre(PublicModel):
    tmdb_id: int = Field(ge=1, le=MAX_TMDB_ID)
    name: str = Field(min_length=1, max_length=100)


class Trailer(PublicModel):
    site: Literal["YouTube"] = "YouTube"
    key: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=500)


class MovieDetailsResponse(PublicModel):
    tmdb_id: int = Field(ge=1, le=MAX_TMDB_ID)
    title: str = Field(min_length=1, max_length=500)
    original_title: str = Field(min_length=1, max_length=500)
    overview: str = Field(max_length=10_000)
    release_date: date | None
    year: int | None = Field(default=None, ge=1800, le=3000)
    runtime_minutes: int | None = Field(default=None, ge=0, le=10_000)
    poster_path: str | None = Field(default=None, max_length=255, pattern=_IMAGE_PATH_PATTERN)
    backdrop_path: str | None = Field(default=None, max_length=255, pattern=_IMAGE_PATH_PATTERN)
    vote_average: float = Field(ge=0, le=10)
    vote_count: int = Field(ge=0)
    genres: tuple[Genre, ...]
    trailer: Trailer | None = None
    attribution: TMDBAttribution = Field(default_factory=TMDBAttribution)


class CastMember(PublicModel):
    tmdb_id: int = Field(ge=1, le=MAX_TMDB_ID)
    name: str = Field(min_length=1, max_length=300)
    character: str = Field(max_length=500)
    profile_path: str | None = Field(default=None, max_length=255, pattern=_IMAGE_PATH_PATTERN)
    order: int = Field(ge=0)


class CrewMember(PublicModel):
    tmdb_id: int = Field(ge=1, le=MAX_TMDB_ID)
    name: str = Field(min_length=1, max_length=300)
    job: str = Field(max_length=300)
    department: str = Field(max_length=300)
    profile_path: str | None = Field(default=None, max_length=255, pattern=_IMAGE_PATH_PATTERN)


class MovieCreditsResponse(PublicModel):
    tmdb_id: int = Field(ge=1, le=MAX_TMDB_ID)
    cast: tuple[CastMember, ...]
    crew: tuple[CrewMember, ...]
    attribution: TMDBAttribution = Field(default_factory=TMDBAttribution)


class StreamingProvider(PublicModel):
    tmdb_provider_id: int = Field(ge=1, le=MAX_TMDB_ID)
    name: str = Field(min_length=1, max_length=300)
    logo_path: str | None = Field(default=None, max_length=255, pattern=_IMAGE_PATH_PATTERN)
    display_priority: int = Field(ge=0)


class MovieProvidersResponse(PublicModel):
    tmdb_id: int = Field(ge=1, le=MAX_TMDB_ID)
    region: Literal["BR"] = "BR"
    streaming: tuple[StreamingProvider, ...]
    free: tuple[StreamingProvider, ...]
    ads: tuple[StreamingProvider, ...]
    rent: tuple[StreamingProvider, ...]
    buy: tuple[StreamingProvider, ...]
    attribution: TMDBAttribution = Field(default_factory=TMDBAttribution)
    availability_attribution: JustWatchAttribution = Field(default_factory=JustWatchAttribution)
