# API: Phase 3

Catalog routes are public and read-only. Account routes are private, JSON-only,
and require a validated Supabase bearer token. Errors use a stable shape:

```json
{"error":"validation_error","request_id":"server-generated-uuid"}
```

## Endpoints

| Method and path | Input | Result | Persistence |
| --- | --- | --- | --- |
| `GET /health` | none | `{"status":"ok"}` only | none |
| `GET /movies/search` | `q` 2–100 chars; `page` 1–500 | bounded movie summaries | never cached or logged |
| `GET /movies/{tmdb_id}` | positive int32 | normalized movie details and safe trailer key | public cache, 24h |
| `GET /movies/{tmdb_id}/credits` | positive int32 | first 20 cast and bounded crew | public cache, 7d |
| `GET /movies/{tmdb_id}/providers` | positive int32 | BR streaming/free/ads/rent/buy groups | public cache, 6h |
| `GET /me` | Supabase bearer token | authenticated user's explicit public-profile schema | private profile row |
| `POST /me` | bearer token, username and display name | creates the token owner's profile | private profile row |
| `GET /me/movies` | bearer token | all personal movie states, newest change first | private library rows |
| `GET /me/watchlist` | bearer token | only `WATCHLIST` entries | private library rows |
| `GET /me/watched` | bearer token | only `WATCHED` entries | private library rows |
| `GET /me/movies/{tmdb_id}` | bearer token and positive int32 TMDB ID | one personal state or generic `404` | private library row |
| `POST /me/movies/{tmdb_id}` | status, optional half-star rating and favorite | idempotently creates or replaces the token owner's state | private library row |
| `PATCH /me/movies/{tmdb_id}` | one or more mutable fields | updates only the token owner's state | private library row |
| `DELETE /me/movies/{tmdb_id}` | bearer token | `204` after removing the token owner's state | deletes private library row |

Catalog routes remain public and read-only. `/me` requires a bearer token that
the API validates against Supabase Auth. Ownership is derived exclusively from
that validated identity; a client-supplied `user_id` is rejected. Neither route
returns `auth_user_id`, e-mail, password data, tokens, or ORM objects.

Library payloads accept no ownership identifier. `status` is one of
`WATCHLIST`, `WATCHED`, or `DROPPED`; `rating` is null or 0.5–5.0 in half-star
steps. Responses expose the public TMDB ID and personal state, but not internal
profile, movie, or relation UUIDs. All library responses are `no-store`.

The API never returns the TMDB credential, raw upstream payload, ORM object, or
arbitrary upstream URL. Image values are validated TMDB paths; the web client
constructs URLs using the fixed `image.tmdb.org` host. Trailer links are built
from a validated YouTube key rather than an upstream URL.

`404`, `429`, TMDB timeouts, invalid upstream data, and missing server
configuration are mapped to bounded public errors. Query strings, request
bodies, IP addresses, authorization headers, cookies, and upstream bodies are
excluded from application logs.

## Local OpenAPI

In development, the schema is available at `/openapi.json`. Interactive docs
and the OpenAPI route are disabled in production. The checked-in API tests are
the executable contract and run without a real TMDB token.
