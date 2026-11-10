# Engineering Register

Last updated: 2026-11-10

| Area | Status | Evidence and limitation |
|---|---|---|
| Ten mandatory contracts | Specified | Machine-readable catalog; only a subset of requirements is executable |
| Strict policy/request parsing | Implemented in reference evaluator | Duplicate keys, non-standard constants, unknown fields, malformed selectors, and oversized inputs rejected |
| Policy evaluator | Experimental reference implementation | Deny-by-default, exact selectors, explicit deny precedence, expiry checks |
| Identity/revocation | Partial local identity signal | Broker derives Linux peer UID; not cryptographic workload identity, UID sharing collapses principals |
| Replay resistance | Local reference control | SQLite atomic one-time UUIDv4 request-ID consumption in broker; rollback/fresh IDs remain possible |
| Evidence ledger | Experimental local format | SHA-256 chain; broker serializes its own appends; no independent checkpoint or anti-rollback |
| Structural verifier | Implemented | Checks repository structure/catalog shape; does not verify deployments |
| Policy publisher authentication | Optional experimental TUF client | python-tuf 7.0.1 verifies metadata signatures, versions, expiry, snapshot consistency, and policy target hashes from a local mirror; bootstrap root is out-of-band; cache rollback protection is an adopter responsibility; merged PR #6 |
| Independent execution broker | Implemented as experimental Linux reference | Separate process, SO_PEERCRED UID mapping, fixed audit.append allowlist, five-minute TTL, UUIDv4 IDs, 32-level JSON cap, bounded inputs, 32-handler cap |
| Broker configuration | Hardened baseline | Rejects symlink/special config files and group/world-writable config/state/socket parent directories |
| Broker and TUF tests | PASS in CI | 57 tests per Python version, 3.11/3.12/3.13; tested head ba950ae7a69ffe77202d786623fdefb662ae1cd1; merged PR #6 as e8a8d1400a601ef4277ed388337f630c06531cf2 |
| CI evidence | PASS | TUF PR runs 42737352852 and 42737349896; main run 42737605525; all matrix jobs passed, including Ruff, structural verification, and JSON checks |
| General tool mediation | Not implemented | No arbitrary tool, filesystem, network, shell, or executable execution |
| Independent review | Not performed | No certification or external audit claim |

## Critical gaps

Cryptographic workload identity and revocation; stronger rollback-resistant TUF cache storage; TUF repository publishing/signing workflow and key management; authenticated request identity and distributed anti-replay; capability-set delegation attenuation; typed protected executor beyond audit append; complete mediation and bypass testing; stronger OS isolation; independently checkpointed evidence; deployment-level conformance; fuzzing/load/penetration testing; independent security review.

## Validation boundary

The CI PASS applies to the exact tested TUF/broker head and workflow. TUF verification is optional and uses an operator-managed local mirror. The broker was merged in commit 1c0295204258a4a92315a9e97dba95a33e8202c4 and the main-branch workflow passed. It does not certify a production deployment, prove all application side effects are mediated, or establish safety. The broker is Linux-only and trusts the host kernel, broker account, and operator-managed configuration/state.
