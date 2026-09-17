# Security and privacy baseline

## Data classification

- Public: TMDB movie, credit, and provider data.
- Private: profile identifiers and the user's personal movie-library state.
- Secret: database credentials, TMDB token, future Supabase service-role key.

## Phase 0 controls

- Secrets are read from environment variables and `.env` files are ignored.
- CORS and trusted hosts use explicit allowlists.
- API logs contain request ID, method, route path, status, and duration only.
- Request bodies, query strings, authorization headers, cookies, and IP addresses
  are not logged.
- Public errors use stable codes and never include traces or configuration.
- API and web responses receive restrictive security headers.
- CI has read-only repository permissions and runs tests, static checks, and
  dependency audits.
- Release and image-publishing jobs grant write permissions only to the job that
  needs them. New third-party actions are pinned to immutable commit SHAs.
- Published images include BuildKit SBOM and provenance; GitHub attestations run
  when the repository visibility and plan support them.

## Threat-model checklist

Each new feature must document who may call it, inputs, outputs, ownership,
visibility, identifier-swapping risk, abuse potential, secret exposure, retention,
and why each new field is necessary.

Authentication and cookie-backed sessions are not part of Phase 0/1. Origin
validation and CSRF tokens must be designed with the Phase 2 authentication work,
before any state-changing authenticated endpoint is released.

## Phase 3 library controls

- Every route resolves the internal profile from the validated Supabase token;
  client-supplied ownership fields are rejected by strict schemas.
- `user_movies` has deny-by-default RLS and owner-only policies for select,
  insert, update, and delete. `movies` reveals rows only when the caller owns a
  related library entry through the Supabase Data API.
- Internal profile, movie, relation, and auth-provider UUIDs are absent from
  library responses; absent and non-owned entries both use a generic `404`.
- Status and half-star constraints exist in both validation and PostgreSQL.
- Deleting a profile cascades its library. Deleting an individual entry removes
  its private state immediately; public TMDB metadata may remain cached by TTL.
