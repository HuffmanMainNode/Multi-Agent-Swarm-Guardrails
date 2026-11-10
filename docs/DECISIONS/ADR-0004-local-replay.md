# ADR-0004: Optional Local Replay Consumption

- Status: Accepted for experimental reference implementation
- Date: 2026-11-10
- Owner: MrCakes931

## Context

The original evaluator accepted the same request repeatedly. Request validity timestamps do not prevent a still-valid request from being replayed. A replay store must provide atomic uniqueness under concurrent callers and fail closed when unavailable.

## Decision

Provide optional local SQLite request-ID consumption. The evaluator records an ALLOW request ID in a transaction before returning ALLOW. A repeated ID returns DENY. SQLite serializes writers; the regression suite tests eight concurrent consumers and requires exactly one winner.

## Trade-offs and assumptions

- Replay protection is disabled unless the caller explicitly supplies a database path.
- The database is local to one installation and is not a distributed coordination mechanism.
- A caller with write access can replace or roll back the database.
- The request ID is not authenticated; an attacker able to mint new IDs can evade duplicate-ID detection.
- An integrator must consume the ID before the protected side effect and must fail closed if the store is unavailable.
- A crash after consumption but before execution can deny a legitimate retry. This favors safety over availability.
- The database does not authenticate principal strings or establish authorization authority.

## Consequences

The CLI reports whether replay protection is enabled. Documentation must not describe the optional local store as universal replay prevention, replay-proof, or anti-rollback. Production deployments need authenticated request identifiers, durable rollback-resistant state, and an independently enforced action boundary.
