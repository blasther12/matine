# Matinê API

FastAPI backend for the privacy-first movie platform. Phase 0 and Phase 1 provide:

- exact `GET /health` liveness response;
- validated environment settings;
- movie search, details, credits and BR watch providers through TMDB;
- async SQLAlchemy, Alembic and a public-data-only `external_cache` table;
- structured, minimized logs and server-generated request IDs;
- public error envelopes, strict host/CORS configuration, and security headers;
- a non-root production container and security-focused tests.

Authentication, user data and Supabase integration remain intentionally outside this phase.

## Local setup

Python 3.12 or newer and PostgreSQL are required.

```bash
python -m venv .venv
python -m pip install -c requirements.lock -e ".[dev]"
```

Copy `.env.example` to `.env` and set every value. Allowlists accept either comma-separated values
or JSON arrays. `ALLOWED_HOSTS` is accepted as a compatibility alias for `TRUSTED_HOSTS`. A local
configuration can use:

```text
APP_ENV=development
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://movie_platform:movie_platform@localhost:5432/movie_platform
CORS_ORIGINS=http://localhost:3000
TRUSTED_HOSTS=localhost,127.0.0.1
TMDB_API_KEY=<TMDB Read Access Token>
```

Run migrations and start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload --no-access-log --no-server-header
```

`GET http://localhost:8000/health` returns exactly:

```json
{"status":"ok"}
```

The health endpoint is deliberately not a dependency/readiness probe and reveals no database,
build, or environment metadata.

Catalog routes are documented in `../../docs/api.md`. Tests mock TMDB and never need a real token.

Interactive API documentation is disabled because the default UI loads third-party assets that
conflict with the API's restrictive content security policy. The OpenAPI JSON is available only
outside production.

## Verification

```bash
pytest
ruff check .
ruff format --check .
mypy app
bandit -c pyproject.toml -r app
pip-audit
```

In production, `DEBUG` must be false, CORS origins must use HTTPS, trusted hosts must be explicit,
the development database URL is rejected, and the TMDB token is required. Configure trusted proxy
handling at the deployment edge; the container does not trust arbitrary forwarded headers.
