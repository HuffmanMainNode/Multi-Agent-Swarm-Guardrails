# ADR-0007: Optional SPIFFE JWT-SVID Workload Identity

- Status: Accepted for experimental integration
- Date: 2026-11-10
- PR: [#8](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/pull/8)
- Merge commit: `afac8e19a9d979158ec048c4261a5a993dce39e5`

## Context

The initial Linux broker derived its principal from `SO_PEERCRED` UID mapping. That is useful local transport provenance but collapses multiple agents that share an OS UID and does not establish a cryptographic workload identity.

MASG should reuse a mature identity protocol rather than inventing its own issuer, key distribution or JWT validation format.

## Decision

Add an optional SPIFFE JWT-SVID mode to the Linux broker:

1. The client presents a bounded JWT-SVID in the broker request.
2. The broker validates it for one operator-configured exact audience through the local SPIFFE Workload API `ValidateJWTSVID` operation.
3. The validated SPIFFE ID becomes the policy principal. A valid identity does not grant authorization; the MASG policy must explicitly allow the exact identity for the fixed `audit.append` operation.
4. The broker validates every request online, does not cache positive identity results, and fails closed if the Workload API is unavailable or rejects the SVID.
5. The broker rejects requests whose expiry exceeds the validated SVID expiry.
6. The token is never copied into policy requests or evidence.
7. Legacy UID mode remains available, but UID-map and SPIFFE modes are mutually exclusive.

The integration uses the optional, exact-pinned community-maintained `py-spiffe==0.4.0` client. MASG does not implement its own JWT signature verifier or trust-bundle manager.

## Security consequences

Positive:
- The policy principal is derived from a cryptographically validated SPIFFE ID rather than a client-supplied name.
- Audience is explicit and checked by the Workload API.
- Every request revalidates against current provider trust material; no MASG identity cache or offline fallback exists.
- Request expiry is bounded by the presented credential's expiry.
- Workload API failure denies the operation.

Residual:
- JWT-SVID is a bearer token. This integration does not bind it to the Unix-socket peer PID/UID or originating process.
- Revocation effectiveness depends on SPIRE/Workload API key and trust-bundle update propagation. No globally instantaneous revocation guarantee.
- The broker trusts the Workload API endpoint, SPIRE configuration, workload attestation selectors, trust domain, keys, clock and socket access controls.
- The optional py-spiffe release is community-maintained and PyPI reports no publishing provenance for 0.4.0. The dependency closure is not hash-pinned by MASG. Review source, artifacts and transitive dependencies before sensitive use.
- CI uses a fake Workload API client. No live SPIRE deployment, key rotation, revocation propagation, or workload-selector integration test is claimed.
- No X.509-SVID/mTLS sender-constrained identity path is implemented.

## Alternatives considered

- Custom JWT/JWKS verification: rejected because MASG should not create a bespoke identity trust stack or manage rotating bundles.
- Trusting a JWT claim without Workload API validation: rejected because token contents alone do not establish signature or trust.
- Caching validated identity: rejected because it complicates revocation/freshness and creates stale authorization state.
- X.509-SVID/mTLS: preferred future direction for sender-constrained identity, but not implemented in this milestone.
- Retaining UID mapping only: remains as a legacy local mode, but does not solve shared-UID identity collapse.

## Follow-up requirements

1. Add a live local SPIRE Agent integration test.
2. Test signing-key rotation, bundle update/removal, expired SVID, wrong audience, workload selector changes and Workload API outage.
3. Evaluate SDK release provenance and hash-pin the complete optional dependency closure or adopt a separately verified client.
4. Implement X.509-SVID/mTLS or equivalent sender-constrained credentials.
5. Add capability-bound delegation only after identity and revocation semantics are independently validated.
