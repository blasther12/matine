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

Supabase Auth owns credentials and session issuance. Next.js stores the SSR
session in secure cookies and forwards only the short-lived access token to
FastAPI. FastAPI validates it with Supabase, maps its subject to `users.id`, and
performs every library query with that server-derived owner.

## Phase boundaries

- Phase 0 establishes builds, tests, migrations, local containers, CI, safe
  configuration, logging, CORS, and response headers.
- Phase 1 adds read-only movie search, details, credits, providers, and a cache
  containing public TMDB data only.
- Phase 2 adds Supabase identity, a minimal private profile, and owner-only RLS.
- Phase 3 adds the `movies` identity table and private `user_movies` state.
  Catalog metadata remains in the public TTL cache and is not duplicated into
  the personal domain.
