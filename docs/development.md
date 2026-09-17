# Development

This guide covers the Phase 0 foundation and its Phase 1-ready local setup. The
application is a modular monolith: Next.js in `apps/web`, FastAPI in `apps/api`,
and PostgreSQL as the only durable service.

## Toolchain

The validated workspace provides:

- Node.js 20.12.2 and pnpm 11.19.0;
- an embedded Python 3.12.14 runtime;
- Docker CLI and Compose, although the Docker daemon may be stopped;
- Git and a local PostgreSQL 15 service on some developer machines.

The ordinary `python` command is not guaranteed to exist. In this Codex
workspace on Windows, locate the embedded runtime without committing a
machine-specific user path:

```powershell
$python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python --version
```

If that path is absent, install or select another Python 3.12 runtime. Do not use
the inaccessible Microsoft Store launcher as evidence that Python is usable.

## Configuration

From the repository root, create an untracked local environment file:

```powershell
Copy-Item .env.example .env
```

Phase 0 does not need a TMDB token. Phase 1 requires a server-side TMDB Read
Access Token in `TMDB_API_KEY`; leave it blank until then. Never add real values
to `.env.example`, source control, screenshots, terminal transcripts, or a
`NEXT_PUBLIC_` variable.

## Containers

Check the daemon before starting the stack:

```powershell
docker info
docker compose config
docker compose up --build
```

If `docker info` cannot connect to the engine, start Docker Desktop and retry.
The first image build or pull needs network access unless every base image and
dependency is already cached.

The Compose database binds only to `127.0.0.1:5432`. A separately installed
PostgreSQL service may already occupy that port. Use a dedicated development
database and credentials; do not point tests at an unknown existing database.
Resolve any port collision with a local Compose override or by deliberately
choosing which local service to run.

Useful checks after startup:

```powershell
docker compose ps
Invoke-RestMethod http://localhost:8000/health
```

The expected health response is `{"status":"ok"}`. The web application is
served on `http://localhost:3000` and the API on `http://localhost:8000`.

## Native backend workflow

Running FastAPI outside its container can shorten the edit-test cycle while
PostgreSQL remains in Compose. From `apps/api`:

```powershell
& $python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
& .\.venv\Scripts\python.exe -m alembic upgrade head
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Use a dedicated `DATABASE_URL` for development and a separate
`TEST_DATABASE_URL` for database tests. A test suite must refuse to run
destructive setup against a URL that is not explicitly marked as a test
database.

Backend verification:

```powershell
& .\.venv\Scripts\python.exe -m pytest
& .\.venv\Scripts\python.exe -m ruff check .
& .\.venv\Scripts\python.exe -m ruff format --check .
& .\.venv\Scripts\python.exe -m bandit -q -r app
& .\.venv\Scripts\python.exe -m pip_audit
```

Tests must not call TMDB or Supabase. Use HTTP transport mocks and local JWT or
JWKS fixtures where those integrations are introduced. PostgreSQL integration
tests should isolate changes with a dedicated database and transactions or a
per-test schema. SQLite is not an adequate substitute for PostgreSQL-specific
constraints, migrations, or future row-level security tests.

## Frontend workflow

From the repository root:

```powershell
pnpm install --frozen-lockfile
pnpm dev
```

Run the complete frontend gate with:

```powershell
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Frontend tests should mock the API boundary. Builds intended to work offline
must not download fonts or assets at build time; prefer bundled or system fonts
instead of remote font loaders. No analytics, third-party cookies, or browser
token storage is needed in Phase 0/1.

## Reproducible offline work

The validated machine has the runtimes but not the FastAPI, pytest, Next.js, or
frontend test packages in a usable offline cache. A first dependency resolution
therefore requires network access or a trusted prebuilt dependency bundle.

For subsequent offline frontend installs, populate a project-specific pnpm
store while connected, then reuse the same lockfile and store:

```powershell
pnpm fetch --frozen-lockfile --store-dir <trusted-store-path>
pnpm install --offline --frozen-lockfile --store-dir <trusted-store-path>
```

For Python, generate a wheelhouse from the locked backend dependencies on a
compatible platform, verify its provenance, and install without an index:

```powershell
& $python -m pip install --no-index --find-links <trusted-wheelhouse-path> -r <locked-requirements-file>
```

Do not commit the store, wheelhouse, virtual environment, or caches. Unit,
authorization, privacy, and integration tests can run without internet once
dependencies are present: mock TMDB and Supabase, and use local PostgreSQL.

`pnpm audit` and `pip-audit` rely on current vulnerability information. Cached
or offline output is useful as a best-effort check, but the connected CI audit
is the authoritative merge gate for newly disclosed vulnerabilities.

## Test layers

1. Pure unit tests cover configuration parsing, domain rules, score
   explainability, and redaction without services.
2. API tests call the ASGI app in-process and replace external integrations.
3. PostgreSQL tests cover migrations, constraints, ownership, visibility, and
   future RLS behavior against a dedicated test database.
4. Frontend component tests use deterministic API fixtures.
5. A small local smoke test verifies `/health`, security headers, and the
   browser-to-API path.

No test fixture should contain real personal data, production tokens, or copied
production records.
