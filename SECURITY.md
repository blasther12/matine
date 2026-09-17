# Security policy

Security and privacy are release requirements for this project. A feature that
works but exposes private data, weakens authorization, or mishandles a secret is
not complete.

The implementation baseline is described in `docs/security.md`; the data flows
and current threats are documented in `docs/data-map.md` and
`docs/threat-model.md`.

## Supported code

Security fixes target the current `main` branch. Phase 0 and Phase 1 are
pre-authentication foundations: they must not collect accounts, profiles,
watching history, preferences, or other personal data. Phase 1 may cache public
TMDB metadata, but it must not build a history of search terms or associate
catalog activity with a person.

Older commits and local modifications are not separately supported. Do not use
the example development configuration in a public deployment.

## Reporting a vulnerability

Report vulnerabilities through a private security-advisory channel provided by
the repository host or directly to the repository owner through a private
channel. Do not publish an exploit, secret, personal data, or detailed bypass in
a public issue. If no private channel is configured, open only a minimal issue
asking the owner to establish one; omit technical details until a private
channel is available.

Include, when safe:

- the affected commit and component;
- prerequisites and a minimal reproduction using synthetic data;
- the expected and observed security boundary;
- likely impact and whether exploitation is active;
- suggested mitigation, if known.

Never attach production credentials, tokens, database dumps, private logs, or
real user data. Maintainers should acknowledge a report promptly, reproduce it
privately, contain exposure, rotate affected credentials, add a regression
test, and disclose details only after a fix is available.

## Secret handling

- Secrets belong in environment variables or a deployment secret manager.
- `.env.example` contains names and safe placeholders only. Real `.env` files
  remain untracked.
- Only intentionally public configuration may use the `NEXT_PUBLIC_` prefix.
  The TMDB credential, database password, and future Supabase service-role key
  are server-only.
- Tokens, cookies, authorization headers, environment dumps, request bodies,
  and query strings must not appear in logs, URLs, traces, build output, or
  error responses.
- A suspected leak requires revocation or rotation; deleting the visible copy
  alone is not sufficient.

The credentials in `docker-compose.yml` are fixed development-only values and
the database port is bound to loopback. They must not be reused in staging or
production.

## Security baseline

Every externally reachable route must have bounded, validated input; explicit
output schemas; stable public errors; safe logging; and an abuse analysis.
Authenticated features introduced in Phase 2 or later additionally require
ownership, visibility, membership, and identifier-swapping tests. The backend,
not browser-provided ownership fields, makes authorization decisions.

Before merging, run the applicable checks documented in
`docs/development.md`: backend tests and static analysis, frontend tests, lint,
type checking, production build, and dependency audits. Dependency audits need
a current advisory source; an offline run cannot establish that dependencies
are free from newly disclosed vulnerabilities.

## Scope boundaries

Phase 0/1 deliberately excludes authentication, cookie sessions, user uploads,
social data, analytics, advertising, and behavioral tracking. Adding any of
these changes the threat model and data map and requires a separate privacy and
security review before implementation.
