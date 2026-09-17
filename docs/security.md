# Security and privacy baseline

## Data classification

- Public: TMDB movie, credit, and provider data.
- Private: no private user data is collected in Phase 0/1.
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

## Threat-model checklist

Each new feature must document who may call it, inputs, outputs, ownership,
visibility, identifier-swapping risk, abuse potential, secret exposure, retention,
and why each new field is necessary.

Authentication and cookie-backed sessions are not part of Phase 0/1. Origin
validation and CSRF tokens must be designed with the Phase 2 authentication work,
before any state-changing authenticated endpoint is released.
