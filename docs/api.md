# Public API: Phase 1

All current routes are public, read-only, JSON-only, and collect no account or
profile data. Errors use a stable shape:

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
