# Engineering Register

Last updated: 2026-11-10

| Area | Status | Evidence and limitation |
|---|---|---|
| Ten mandatory contracts | Specified | Machine-readable catalog; only a subset of requirements is executable |
| Strict policy/request parsing | Implemented in reference evaluator | Duplicate keys, non-standard constants, unknown fields, malformed selectors, and oversized inputs rejected |
| Policy evaluator | Experimental reference implementation | Deny-by-default, exact selectors, explicit deny precedence, expiry checks |
| Identity/revocation | Experimental SPIFFE JWT-SVID validation option | Broker validates each presented token through the local Workload API for a fixed audience; exact SPIFFE ID becomes policy principal; legacy UID mode remains; bearer-token and provider trust limits documented |
| Replay resistance | Local reference control | SQLite atomic one-time UUIDv4 request-ID consumption in broker; rollback/fresh IDs remain possible |
| Evidence ledger | Experimental local format | SHA-256 chain; broker serializes its own appends; no independent checkpoint or anti-rollback |
| Structural verifier | Implemented | Checks repository structure/catalog shape; does not verify deployments |
| Policy publisher authentication | Optional experimental TUF client | python-tuf 7.0.1 verifies metadata signatures, versions, expiry, snapshot consistency, and policy target hashes from a local mirror; bootstrap root is out-of-band; cache rollback protection is an adopter responsibility; merged PR #6 |
| Independent execution broker | Implemented as experimental Linux reference | Separate process, SO_PEERCRED transport provenance, UID mapping or optional SPIFFE JWT-SVID principal, fixed audit.append allowlist, five-minute TTL, UUIDv4 IDs, bounded inputs, 32-handler cap |
| Broker configuration | Hardened baseline | Rejects symlink/special config files and group/world-writable config/state/socket parent directories |
| Broker and TUF tests | PASS in CI | 57 tests per Python version, 3.11/3.12/3.13; tested head ba950ae7a69ffe77202d786623fdefb662ae1cd1; merged PR #6 as e8a8d1400a601ef4277ed388337f630c06531cf2 |
| SPIFFE adapter tests | Pending CI | Fake Workload API tests cover bounded token validation, audience, endpoint socket, identity derivation, expiry binding and fail-closed behavior; no live SPIRE test yet |
| General tool mediation | Not implemented | No arbitrary tool, filesystem, network, shell, or executable execution |
| Independent review | Not performed | No certification or external audit claim |

## Critical gaps

Sender-constrained identity (X.509-SVID/mTLS); live SPIRE rotation/revocation tests; stronger rollback-resistant TUF cache storage; TUF repository publishing/signing workflow and key management; authenticated request identity and distributed anti-replay; capability-set delegation attenuation; typed protected executor beyond audit append; complete mediation and bypass testing; stronger OS isolation; independently checkpointed evidence; deployment-level conformance; fuzzing/load/penetration testing; independent security review.

## Validation boundary

The prior CI PASS applies to the exact tested TUF/broker head and workflow. The SPIFFE adapter is on a review branch and has not passed CI yet. The optional integration depends on the Workload API, provider trust state and an optional third-party Python SDK. It does not certify a production deployment, prove all application side effects are mediated, or establish safety.
