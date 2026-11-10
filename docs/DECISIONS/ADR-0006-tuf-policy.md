# ADR-0006: TUF-Verified Policy Distribution

- Status: Accepted for optional experimental client integration
- Date: 2026-11-10
- Owner: MrCakes931

## Context

The broker previously loaded an operator-managed policy file without cryptographic publisher authentication, metadata freshness, or rollback-aware update handling. A detached signature alone does not provide a complete update framework.

## Decision

Use python-tuf's ngclient Updater for optional policy retrieval from a local TUF mirror. The adopter supplies an out-of-band trusted root bootstrap, persistent protected metadata cache, local mirror directory, and target path. TUF verifies metadata signatures, role thresholds, version progression, expiry, snapshot consistency, and target hashes/lengths. MASG then loads the verified target through its existing strict policy parser.

The local fetcher implements TUF's FetcherInterface and maps the synthetic HTTPS origin to a directory. It does not make network requests. No MASG-hosted service is introduced. TUF is an optional dependency; static policy mode remains supported.

## Security constraints

- Initial root metadata must be provisioned out-of-band.
- Private signing keys must never be committed to the repository.
- Cache metadata must be persistent and protected from agent writes and rollback.
- TUF expiry relies on a sufficiently trustworthy host clock.
- One active Updater per cache is supported; concurrent broker instances sharing a cache are not.
- Any verification failure prevents broker startup; no unsigned fallback.
- The repository does not implement TUF repository publishing or signing-key management.

## Consequences

Policy publisher authentication and metadata update verification can be adopted without MASG inventing cryptography or requiring a hosted service. Rollback protection depends on retained trusted metadata and protected local storage. Static policy mode remains unauthenticated and must be treated as a development/operator-trust mode.
