# Data map and retention

This inventory describes Phases 0–3. Phase 3 introduces the minimum private
state required for a personal movie library. It does not store e-mail, password
material, tokens, viewing dates, review text, lists, streaming preferences,
social graphs, or inferred taste profiles.

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
| Supabase auth user UUID | 2, bind a validated identity to one internal profile | Private identifier | PostgreSQL `users.auth_user_id` | Account lifetime; cascade deletion with the Supabase identity | Profile owner and backend only |
| Internal profile UUID | 2, stable ownership key without exposing the auth provider ID | Private identifier | PostgreSQL `users.id` | Account lifetime | Profile owner and backend only |
| Username and display name | 2, user-selected profile identity | Private by default | PostgreSQL `users` | Account lifetime; user-controlled deletion arrives before social publication | Profile owner and backend only |
| Avatar URL | 2, optional profile presentation | Private by default | PostgreSQL `users`; image bytes are not copied | Account lifetime or until changed | Profile owner and backend only |
| TMDB ID associated with a library entry | 3, identify the catalog movie chosen by the user | Private behavioral data in this context | PostgreSQL `movies` joined to `user_movies` | Until the user removes the entry or account deletion cascades | Profile owner and backend only |
| Library status (`WATCHLIST`, `WATCHED`, `DROPPED`) | 3, remember the user's explicit movie state | Private behavioral data | PostgreSQL `user_movies` | Until changed/removed or account deletion cascades | Profile owner and backend only |
| Half-star rating and favorite flag | 3, explicit personal evaluation and shortcut | Private preference data | PostgreSQL `user_movies` | Until changed/removed or account deletion cascades | Profile owner and backend only |
| Library creation/update timestamps | 3, ordering and audit of the user's own state | Private metadata | PostgreSQL `user_movies` | Same as the library entry | Profile owner and backend only |

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

Phase 2 uses secure Supabase SSR session cookies and does not store identity in
`localStorage`, `sessionStorage`, or IndexedDB. Do not add analytics,
advertising pixels, fingerprinting, third-party cookies, or hidden tracking.
The service-role credential is not used for normal user requests; the backend
validates the bearer token with the anon/publishable credential and derives
ownership from the validated Supabase UUID.

## Local persistence and deletion

The Compose PostgreSQL volume persists schema and public cache between restarts.
It remains until a developer explicitly removes that local volume; removal is a
destructive development action and should never target an unverified database.
Production backups that contain Phase 2/3 personal rows inherit the same access
controls and must use the shortest operationally viable retention.

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
