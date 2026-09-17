# Architecture

## Shape

The product is a modular monolith in one repository:

- `apps/web`: Next.js App Router user interface.
- `apps/api`: FastAPI application containing domain modules and external integrations.
- `packages/shared`: a future home for generated API contracts only.
- PostgreSQL: durable domain data and public TMDB response cache.

Requests flow from a router to a service and then to a repository or integration.
Interfaces and background infrastructure are introduced only when a concrete use
case requires them.

## Trust boundaries

```text
Browser -> Next.js -> FastAPI -> PostgreSQL
                         |
                         +----> TMDB
```

The browser never receives database credentials, the Supabase service-role key,
or the TMDB token. FastAPI exposes explicit response schemas instead of upstream
payloads or ORM instances.

## Phase boundaries

- Phase 0 establishes builds, tests, migrations, local containers, CI, safe
  configuration, logging, CORS, and response headers.
- Phase 1 adds read-only movie search, details, credits, providers, and a cache
  containing public TMDB data only.
- Authentication and all user data remain deferred to Phase 2. No placeholder
  identity fields are collected early.
