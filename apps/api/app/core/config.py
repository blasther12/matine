import json
from functools import lru_cache
from typing import Literal, Self
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
VercelEnvironment = Literal["development", "preview", "production"]

DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://movie_platform:movie_platform@localhost:5432/movie_platform"
)
_DATABASE_SCHEMES = {"postgres", "postgresql", "postgresql+asyncpg"}


def _parse_list(value: str, *, field_name: str) -> tuple[str, ...]:
    stripped = value.strip()
    candidates: list[str]
    if stripped.startswith("["):
        try:
            decoded: object = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{field_name} must be a JSON array or comma-separated list") from exc
        if not isinstance(decoded, list) or not all(isinstance(item, str) for item in decoded):
            raise ValueError(f"{field_name} JSON value must be an array of strings")
        candidates = [item for item in decoded if isinstance(item, str)]
    else:
        candidates = stripped.split(",")

    items = tuple(dict.fromkeys(item.strip() for item in candidates if item.strip()))
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    return items


def _validated_origin(origin: str, *, production: bool) -> str:
    if origin == "*":
        raise ValueError("CORS origins must be explicit; wildcard is not allowed")

    try:
        parsed = urlsplit(origin)
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("CORS origin is not a valid origin") from exc

    if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
        raise ValueError("CORS origin must use http or https and include a host")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("CORS origin must not contain credentials")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("CORS origin must not contain a path, query, or fragment")
    if production and parsed.scheme != "https":
        raise ValueError("production CORS origins must use https")

    return origin.rstrip("/")


def _validated_host(host: str) -> str:
    normalized = host.strip().lower()
    if (
        not normalized
        or normalized == "*"
        or "*" in normalized
        or "://" in normalized
        or "/" in normalized
        or any(character.isspace() for character in normalized)
    ):
        raise ValueError("trusted hosts must be explicit hostnames without scheme or path")

    try:
        parsed = urlsplit(f"//{normalized}")
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("trusted host is not valid") from exc

    if (
        parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("trusted host is not valid")

    return parsed.hostname.lower()


def _is_local_host(host: str | None) -> bool:
    return host in {"localhost", "127.0.0.1", "::1", "testserver"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    app_env: Environment = Field(default="development", validation_alias="APP_ENV")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: LogLevel = Field(default="INFO", validation_alias="LOG_LEVEL")
    vercel_env: VercelEnvironment | None = Field(
        default=None,
        validation_alias="VERCEL_ENV",
        repr=False,
    )
    vercel_url: str | None = Field(default=None, validation_alias="VERCEL_URL", repr=False)
    vercel_branch_url: str | None = Field(
        default=None,
        validation_alias="VERCEL_BRANCH_URL",
        repr=False,
    )
    vercel_project_production_url: str | None = Field(
        default=None,
        validation_alias="VERCEL_PROJECT_PRODUCTION_URL",
        repr=False,
    )
    database_url: SecretStr = Field(
        default=SecretStr(DEFAULT_DATABASE_URL),
        validation_alias="DATABASE_URL",
        repr=False,
    )
    cors_origins_csv: str = Field(
        default="http://localhost:3000",
        validation_alias="CORS_ORIGINS",
        repr=False,
    )
    trusted_hosts_csv: str = Field(
        default="localhost,127.0.0.1,testserver",
        validation_alias=AliasChoices("TRUSTED_HOSTS", "ALLOWED_HOSTS"),
        repr=False,
    )
    tmdb_api_key: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="TMDB_API_KEY",
        repr=False,
    )
    supabase_url: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
        repr=False,
    )
    supabase_anon_key: SecretStr = Field(
        default=SecretStr(""),
        validation_alias=AliasChoices("SUPABASE_PUBLISHABLE_KEY", "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY"),
        repr=False,
    )
    rate_limit_requests: int = Field(
        default=30,
        ge=1,
        le=10_000,
        validation_alias="RATE_LIMIT_REQUESTS",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        le=3_600,
        validation_alias="RATE_LIMIT_WINDOW_SECONDS",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        raw_value = value.get_secret_value()
        parsed = urlsplit(raw_value)
        if (
            parsed.scheme not in _DATABASE_SCHEMES
            or parsed.hostname is None
            or not parsed.path.strip("/")
            or parsed.fragment
        ):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL connection URL")
        return value

    @property
    def cors_origins(self) -> tuple[str, ...]:
        configured = _parse_list(self.cors_origins_csv, field_name="CORS_ORIGINS")
        if self.vercel_env is not None:
            configured = tuple(
                origin for origin in configured if not _is_local_host(urlsplit(origin).hostname)
            )
        vercel_origins = tuple(f"https://{host}" for host in self.vercel_hosts)
        return tuple(
            dict.fromkeys(
                _validated_origin(origin, production=self.is_production)
                for origin in (*configured, *vercel_origins)
            )
        )

    @property
    def trusted_hosts(self) -> tuple[str, ...]:
        configured = _parse_list(self.trusted_hosts_csv, field_name="TRUSTED_HOSTS")
        if self.vercel_env is not None:
            configured = tuple(
                host for host in configured if not _is_local_host(_validated_host(host))
            )
        return tuple(
            dict.fromkeys(_validated_host(host) for host in (*configured, *self.vercel_hosts))
        )

    @property
    def vercel_hosts(self) -> tuple[str, ...]:
        candidates = (
            self.vercel_url,
            self.vercel_branch_url,
            self.vercel_project_production_url,
        )
        return tuple(
            dict.fromkeys(_validated_host(host) for host in candidates if host is not None)
        )

    @property
    def database_dsn(self) -> str:
        parsed = urlsplit(self.database_url.get_secret_value())
        query = [
            ("ssl" if key == "sslmode" else key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        ]
        return urlunsplit(
            (
                "postgresql+asyncpg",
                parsed.netloc,
                parsed.path,
                urlencode(query),
                "",
            )
        )

    @property
    def tmdb_token(self) -> str:
        return self.tmdb_api_key.get_secret_value()

    @property
    def supabase_origin(self) -> str:
        value = self.supabase_url.rstrip("/")
        if not value:
            return ""
        return _validated_origin(value, production=self.is_production)

    @property
    def supabase_public_key(self) -> str:
        return self.supabase_anon_key.get_secret_value()

    @property
    def is_production(self) -> bool:
        return self.app_env == "production" or self.vercel_env == "production"

    @property
    def runtime_environment(self) -> Environment:
        return "production" if self.is_production else self.app_env

    @model_validator(mode="after")
    def validate_environment_safety(self) -> Self:
        origins = self.cors_origins
        hosts = self.trusted_hosts

        if self.is_production:
            if self.debug:
                raise ValueError("DEBUG must be disabled in production")
            if self.database_dsn == DEFAULT_DATABASE_URL:
                raise ValueError("production must not use the development database URL")
            if not self.tmdb_token:
                raise ValueError("TMDB_API_KEY is required in production")
            if not self.supabase_origin or not self.supabase_public_key:
                raise ValueError("Supabase URL and public key are required in production")
            if any(_is_local_host(host) for host in hosts):
                raise ValueError("production TRUSTED_HOSTS must not contain local hosts")
            if any(_is_local_host(urlsplit(origin).hostname) for origin in origins):
                raise ValueError("production CORS_ORIGINS must not contain local hosts")

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
