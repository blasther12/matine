# Threat model: Phase 0 and Phase 1

## Scope and assumptions

This model covers the public foundation, health endpoint, local PostgreSQL,
Next.js-to-FastAPI boundary, and the Phase 1 TMDB catalog proxy/cache. There is
no authentication or personal movie data in these phases. Production terminates
TLS at a trusted edge; local ports bind to loopback where possible.

The browser and every HTTP input are untrusted. TMDB is trusted to provide
catalog data but its payloads are still untrusted input. Source dependencies,
container images, CI actions, developer machines, and deployment configuration
are supply-chain or operator trust boundaries, not inherently safe content.

Authentication, cookies, CSRF, user ownership, social visibility, account
deletion, and row-level security are deliberately deferred. They must be added
to this model before Phase 2 begins, not retrofitted after private endpoints are
released.

## Assets

- TMDB token, database credentials, and future Supabase secrets;
- integrity and availability of API responses and the public catalog cache;
- confidentiality of operational configuration and logs;
- repository, dependency lockfiles, CI jobs, and deployment pipeline;
- the privacy promise that Phase 0/1 creates no behavioral or personal profile.

## Trust boundaries

```text
Untrusted browser
      |
      v
Next.js / deployment edge
      |
      v
FastAPI ----------------------> TMDB
      |
      v
PostgreSQL

Developer/CI pipeline -------> build artifacts and deployment
```

Data is revalidated when it crosses each boundary. A successful request to one
component does not grant implicit trust at the next component.

## Threats and controls

| Threat or abuse case | Impact | Required controls | Verification |
| --- | --- | --- | --- |
| Server secret included in a browser bundle | TMDB, database, or administrative access | Keep secrets server-side; allow only public values under `NEXT_PUBLIC_`; review built output and environment mapping | Build test and secret-pattern scan |
| Secret, query, or private content written to logs/errors | Credential or behavioral-data disclosure | Allowlisted log fields; route templates rather than URLs; stable public errors; no bodies, query strings, headers, cookies, IPs, or stack traces | Redaction and error-response tests |
| API used as an arbitrary outbound proxy | SSRF and internal network access | Fixed TMDB base origin and allowlisted paths; numeric ID validation; never accept a caller-supplied URL | Reject alternate schemes, hosts, and malformed IDs |
| Automated search or catalog scraping exhausts TMDB quota | Availability loss and unexpected cost | Per-route rate limits, bounded pagination, frontend debounce, public-data cache, upstream timeouts, and controlled retries | Rate-limit and timeout tests |
| SQL injection or unsafe dynamic filters | Database compromise | Pydantic validation, SQLAlchemy parameterization, allowlisted sort/filter fields, no concatenated SQL | Malicious-input repository/API tests |
| Script content from queries or TMDB executes in the UI | XSS and credential theft in later phases | Render content as text; avoid arbitrary HTML and `dangerouslySetInnerHTML`; restrictive CSP | Component tests with hostile strings and header test |
| Raw movie searches become a behavioral history | Privacy breach despite no accounts | Never log or persist search text; do not cache by raw query; do not add fingerprinting identifiers | Log-capture and persistence tests |
| Cache key collision, poisoning, or mixing personal state | Incorrect output or private-data leak later | Namespaced provider/resource/version keys; cache only validated public TMDB payloads; keep personal state out of `ExternalCache`; enforce TTL | Cache-isolation and expiry tests |
| Oversized, malformed, or slow upstream response | Memory/worker exhaustion and invalid output | Connect/read timeouts, response-size bounds, explicit upstream schemas, bounded error details, no unbounded retry loop | Mocked slow, invalid, and oversized responses |
| Cross-origin or forged host access | Expanded browser attack surface and cache poisoning | Exact production CORS and trusted-host allowlists; no wildcard on authenticated routes; validate environment configuration | Origin/host allowlist tests |
| Missing security headers or framing protection | XSS, content sniffing, clickjacking, referrer leakage | CSP with `frame-ancestors`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and production HSTS | Header test on web and API responses |
| Public errors expose internals | Filesystem, SQL, dependency, or secret disclosure | Map exceptions to stable codes; retain diagnostic detail only in redacted operator logs | Force configuration, database, and upstream failures |
| Development database exposed beyond the machine | Data/configuration compromise | Bind host port to `127.0.0.1`; development-only credentials; unique production secrets; least privilege | Inspect Compose config and deployment configuration |
| Compromised dependency, image, or CI action | Build or runtime compromise | Lock dependencies, minimize packages, review updates, read-only CI permissions, static checks, connected advisory audits, trusted image sources | Reproducible install, CI review, `pip-audit` and `pnpm audit` |
| Accidental collection of identity before Phase 2 | Unreviewed personal-data exposure | No auth/profile fields, analytics, tracking, uploads, or Supabase calls in Phase 0/1; migration data-necessity gate | Schema and network-call review |

## Authorization position

Phase 0/1 exposes public catalog behavior only. It must not simulate identity
with a request `user_id`, placeholder owner, browser header, or query parameter.
The first authenticated feature must derive the current user from a verified
Supabase session and then enforce resource ownership, visibility, and circle
membership in the backend.

Before Phase 2, add tests proving at minimum:

- unauthenticated callers cannot access `/me`;
- a payload `user_id` cannot select ownership;
- one user cannot read or modify another user's private resource;
- private resource existence is not leaked through distinguishable responses;
- private activity and recommendation reasons do not expose private inputs;
- RLS defaults to deny and is tested through non-administrative database roles.

## Abuse and failure behavior

Validation failures return a bounded 4xx response. TMDB timeouts and invalid
responses return a stable upstream error and must not reveal the upstream token
or raw payload. Database failures return a stable service error. Retries, if
used, are few, time-bounded, and limited to safe idempotent requests.

Health checks expose only availability, not dependency versions, environment
values, database names, or stack traces. Rate-limit responses do not disclose
internal counters for other callers.

## Residual risks and accepted constraints

- The first Docker image pull and first dependency installation require a
  trusted network unless artifacts were pre-cached and verified.
- Offline dependency audits cannot detect advisories published after the local
  advisory data was captured; connected CI remains required before release.
- TMDB necessarily receives the catalog query and the backend's outbound IP.
  The system minimizes that disclosure and does not attach a user identity.
- Development Compose credentials are intentionally low-value and local-only;
  they are unacceptable in a shared or public environment.
- Per-process rate limiting protects a single Phase 0 deployment but is not a
  global quota across replicas. Reassess only when horizontal deployment makes
  that limitation concrete.

## Review triggers

Update this model before adding authentication, cookies, any user table,
uploads, public profiles, social graphs, notifications, recommendation inputs,
analytics, a new third party, a new public write endpoint, or a new deployment
trust boundary. Each review must also update the data map, retention behavior,
authorization tests, and incident impact.
