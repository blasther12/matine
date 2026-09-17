# TMDB integration

## Configuration

Create a TMDB API Read Access Token and set it server-side:

```text
TMDB_API_KEY=<read-access-token>
```

The historical variable name is retained for compatibility with the project
brief. The implementation sends its value only in the `Authorization: Bearer`
header to the fixed origin `https://api.themoviedb.org/3`. It never places the
token in a URL, browser bundle, log, cache key, response, or `NEXT_PUBLIC_*`
variable. Production configuration fails closed when the token is absent.

Language is fixed to `pt-BR`, provider region to `BR`, and movie search always
uses `include_adult=false`. Callers cannot supply an upstream host, path,
language, region, or arbitrary append operation.

## Cache and privacy

`external_cache` contains only normalized public catalog responses. Keys are
versioned and based on numeric TMDB IDs:

```text
movie:details:v1:pt-BR:{id}   24 hours
movie:credits:v1:pt-BR:{id}    7 days
movie:providers:v1:BR:{id}     6 hours
```

Search terms and search responses are intentionally not persisted. Expired
rows stop being readable immediately. The migration revokes table access from
Supabase `anon` and `authenticated` roles when those roles exist.

## Attribution and limitations

This product uses the TMDB API but is not endorsed or certified by TMDB.
Streaming availability is supplied by JustWatch through TMDB and is explicitly
attributed in the interface. Availability may lag provider changes; users
should verify an offer before purchasing or subscribing.

The local in-memory limiter is per process and retains only salted identifiers
for the active time window. A multi-replica production deployment should also
enforce rate limits at the trusted edge.

## Tests

`pytest` uses `respx` and synthetic fixtures to verify Bearer authentication,
fixed host/locale, input bounds, search non-persistence, cache hit/expiry,
provider region, rate limiting, response bounds, and sanitized upstream errors.
No test calls the live TMDB API.
