from pydantic import BaseModel, ConfigDict, Field

_MAX_TMDB_ID = 2_147_483_647


class TMDBModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class TMDBMovieSummary(TMDBModel):
    id: int = Field(ge=1, le=_MAX_TMDB_ID)
    title: str
    original_title: str
    overview: str = ""
    release_date: str = ""
    poster_path: str | None = None
    vote_average: float = Field(default=0, ge=0, le=10)


class TMDBSearchResponse(TMDBModel):
    page: int = Field(ge=1, le=500)
    total_pages: int = Field(ge=0, le=500)
    total_results: int = Field(ge=0)
    results: list[TMDBMovieSummary] = Field(default_factory=list, max_length=20)


class TMDBGenre(TMDBModel):
    id: int = Field(ge=1, le=_MAX_TMDB_ID)
    name: str


class TMDBVideo(TMDBModel):
    key: str = Field(min_length=1, max_length=128)
    name: str = Field(default="Trailer", max_length=500)
    site: str = Field(default="", max_length=50)
    type: str = Field(default="", max_length=50)
    official: bool = False


class TMDBVideosResponse(TMDBModel):
    results: list[TMDBVideo] = Field(default_factory=list, max_length=500)


class TMDBMovieDetails(TMDBModel):
    id: int = Field(ge=1, le=_MAX_TMDB_ID)
    title: str
    original_title: str
    overview: str = ""
    release_date: str = ""
    runtime: int | None = Field(default=None, ge=0, le=10_000)
    poster_path: str | None = None
    backdrop_path: str | None = None
    vote_average: float = Field(default=0, ge=0, le=10)
    vote_count: int = Field(default=0, ge=0)
    genres: list[TMDBGenre] = Field(default_factory=list, max_length=100)
    videos: TMDBVideosResponse = Field(default_factory=TMDBVideosResponse)


class TMDBCastMember(TMDBModel):
    id: int = Field(ge=1, le=_MAX_TMDB_ID)
    name: str
    character: str = ""
    profile_path: str | None = None
    order: int = Field(default=0, ge=0)


class TMDBCrewMember(TMDBModel):
    id: int = Field(ge=1, le=_MAX_TMDB_ID)
    name: str
    job: str = ""
    department: str = ""
    profile_path: str | None = None


class TMDBCreditsResponse(TMDBModel):
    id: int = Field(ge=1, le=_MAX_TMDB_ID)
    cast: list[TMDBCastMember] = Field(default_factory=list, max_length=5_000)
    crew: list[TMDBCrewMember] = Field(default_factory=list, max_length=5_000)


class TMDBProvider(TMDBModel):
    provider_id: int = Field(ge=1, le=_MAX_TMDB_ID)
    provider_name: str
    logo_path: str | None = None
    display_priority: int = Field(default=0, ge=0)


class TMDBRegionProviders(TMDBModel):
    flatrate: list[TMDBProvider] = Field(default_factory=list, max_length=500)
    free: list[TMDBProvider] = Field(default_factory=list, max_length=500)
    ads: list[TMDBProvider] = Field(default_factory=list, max_length=500)
    rent: list[TMDBProvider] = Field(default_factory=list, max_length=500)
    buy: list[TMDBProvider] = Field(default_factory=list, max_length=500)


class TMDBProvidersResponse(TMDBModel):
    id: int = Field(ge=1, le=_MAX_TMDB_ID)
    results: dict[str, TMDBRegionProviders] = Field(default_factory=dict)
