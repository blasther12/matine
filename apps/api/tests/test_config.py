import pytest
from pydantic import ValidationError

from app.core.config import Settings

_PRODUCTION_DATABASE_URL = "postgresql+asyncpg://api:strong-local-placeholder@db.internal:5432/app"


def test_database_secret_is_not_exposed_by_repr() -> None:
    password = "never-print-this-password"
    settings = Settings(
        _env_file=None,
        database_url=f"postgresql+asyncpg://api:{password}@localhost:5432/app",
    )

    assert password not in repr(settings)


def test_database_rejects_non_postgres_urls() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="sqlite:///tmp/app.db")


def test_supabase_postgres_url_is_normalized_for_asyncpg() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql://api:password@db.example.com:6543/app?sslmode=require",
    )

    assert settings.database_dsn == (
        "postgresql+asyncpg://api:password@db.example.com:6543/app?ssl=require"
    )


@pytest.mark.parametrize(
    ("overrides", "expected_message"),
    [
        ({"debug": True}, "DEBUG must be disabled"),
        ({"cors_origins_csv": "*"}, "wildcard is not allowed"),
        ({"cors_origins_csv": "http://web.example.com"}, "must use https"),
        ({"trusted_hosts_csv": "*"}, "must be explicit"),
    ],
)
def test_unsafe_production_settings_fail_closed(
    overrides: dict[str, object], expected_message: str
) -> None:
    values: dict[str, object] = {
        "_env_file": None,
        "app_env": "production",
        "debug": False,
        "database_url": _PRODUCTION_DATABASE_URL,
        "cors_origins_csv": "https://web.example.com",
        "trusted_hosts_csv": "api.example.com",
    }
    values.update(overrides)

    with pytest.raises(ValidationError, match=expected_message):
        Settings(**values)


def test_csv_allowlists_are_trimmed_and_deduplicated() -> None:
    settings = Settings(
        _env_file=None,
        cors_origins_csv="http://localhost:3000, http://localhost:3000",
        trusted_hosts_csv="testserver, TESTSERVER:8000, localhost",
    )

    assert settings.cors_origins == ("http://localhost:3000",)
    assert settings.trusted_hosts == ("testserver", "localhost")


def test_json_allowlist_format_is_supported() -> None:
    settings = Settings(
        _env_file=None,
        cors_origins_csv='["http://localhost:3000"]',
        trusted_hosts_csv='["testserver", "localhost"]',
    )

    assert settings.cors_origins == ("http://localhost:3000",)
    assert settings.trusted_hosts == ("testserver", "localhost")
