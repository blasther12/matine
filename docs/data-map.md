# Data map and retention

This inventory describes Phase 0 and the planned Phase 1 catalog integration.
Neither phase creates accounts or stores personal profiles, watch history,
ratings, reviews, lists, streaming preferences, social graphs, taste profiles,
or authentication data.

## Data flows

```text
Browser
  |  public requests; no auth cookie or analytics identifier
  v
Next.js web application
  |  validated API request
  v
FastAPI
  |---------------------> PostgreSQL
  |                       schema + public TMDB cache only
  |
  +---------------------> TMDB (Phase 1)
                          minimum catalog request only
```

TMDB sees the backend's outbound connection, not a deliberately forwarded
browser IP. The API must not forward cookies, authorization headers, user-agent
identifiers, or unrelated request metadata to TMDB.

## Inventory

| Data | Phase and purpose | Classification | Stored where | Retention | Access |
| --- | --- | --- | --- | --- | --- |
| Application settings such as allowed origins and log level | 0, runtime configuration | Internal | Process memory; optional untracked local `.env` | Process lifetime; local file until developer removes it | Application operators |
| Database, TMDB, and future Supabase credentials | 0/1, service access | Secret | Environment or deployment secret manager; process memory | Only while required; rotate on suspected disclosure | Backend/deployment only |
| Health status | 0, availability check | Public | Not persisted | Request lifetime | Anyone able to reach `/health` |
| Request ID, method, route template, status, duration | 0, diagnostics | Internal operational metadata | Structured stdout and hosting logs | Application stores none; configure platform retention to at most 14 days | Operators with log access |
| Raw path parameters and query values | 0/1, fulfill a request | Potentially identifying if misused | Request memory only | Request lifetime | Handling endpoint only |
| Movie search text | 1, query TMDB | Potential behavioral data | Request memory only; forwarded minimally to TMDB | Request lifetime; do not persist or include in logs | Request handler and TMDB |
| TMDB movie ID and public movie, credit, person, provider, trending, and collection metadata | 1, catalog and latency reduction | Public external data | API response and bounded PostgreSQL cache | TTL schedule below | Public API clients and backend |
| Cache key, provider name, creation and expiry timestamps | 1, cache operation | Internal metadata | PostgreSQL | Delete within 24 hours after expiry | Backend only |
| Migration version and database health metadata | 0, schema management | Internal | PostgreSQL | Life of the environment | Backend and operators |
| Synthetic test fixtures | 0/1, verification | Synthetic | Test process or dedicated test database | Delete at test completion; failed-run artifacts at most 7 days | Developers and CI |
| Source, test output, and CI logs | 0, build verification | Internal | Repository host/CI | Use shortest host setting; target at most 30 days and publish no secret-bearing artifacts | Repository maintainers |

Routes must be logged as templates such as `/movies/{tmdb_id}`, not raw URLs.
Query strings, request and response bodies, IP addresses, cookies,
`Authorization`, referrers, user agents, and environment dumps are excluded from
application logs.

## TMDB cache schedule

Only public upstream data may enter `ExternalCache`. Personal state and search
history must never share this cache.

| Cache content | Maximum TTL |
| --- | --- |
| Trending or other rapidly changing fixed feeds | 1 hour |
| Provider availability for region `BR` | 6 hours |
| Movie details | 24 hours |
| Credits and person details | 7 days |

Search responses should not be cached by raw query. Numeric TMDB identifiers and
fixed public feed keys are preferred because they do not create a record of what
someone searched for. Expired cache rows should become unreadable immediately
and be removed by a bounded cleanup job within 24 hours.

## Browser and third parties

Phase 0/1 sets no authentication cookie and requires no `localStorage`,
`sessionStorage`, or IndexedDB identity. Do not add analytics, advertising
pixels, fingerprinting, third-party cookies, or hidden tracking. Poster and
backdrop delivery should disclose only the minimum catalog request required by
the selected TMDB image delivery approach.

Supabase variables are placeholders for Phase 2. Phase 0/1 must not send data to
Supabase or use its service-role credential.

## Local persistence and deletion

The Compose PostgreSQL volume persists schema and public cache between restarts.
It remains until a developer explicitly removes that local volume; removal is a
destructive development action and should never target an unverified database.
Phase 0/1 does not require production backups of personal data because none is
collected.

Temporary files must use isolated storage and be deleted at the end of the
operation. The application does not accept uploads in Phase 0/1.

## Gate for new fields

Before a migration adds any user-related field, record:

- field and purpose;
- feature that requires it;
- classification and default visibility;
- source, recipients, and authorized roles;
- retention and deletion behavior;
- why an existing field or transient computation is insufficient.

If those questions do not establish necessity, do not store the field. Phase 2
must update this map before introducing identity, sessions, ownership, or RLS
policies.
