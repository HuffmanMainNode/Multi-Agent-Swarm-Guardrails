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
| Independent execution broker | Implemented as experimental Linux reference | Separate process, SO_PEERCRED UID mapping, fixed audit.append allowlist, five-minute TTL, UUIDv4 IDs, 32-level JSON cap, bounded inputs, 32-handler cap |
| Broker configuration | Hardened baseline | Rejects symlink/special config files and group/world-writable config/state/socket parent directories |
| Broker tests | PASS in CI | 46 tests per Python version, 3.11/3.12/3.13; final tested head 6885d489f8aa971c5d409c8de5753a539ef540e5 |
| CI evidence | PASS | Runs 42735881467 and 42735881291; all matrix jobs passed |
| General tool mediation | Not implemented | No arbitrary tool, filesystem, network, shell, or executable execution |
| Independent review | Not performed | No certification or external audit claim |

## Critical gaps

Cryptographic workload identity and revocation; signed policy provenance and anti-rollback; authenticated request identity and distributed anti-replay; capability-set delegation attenuation; typed protected executor beyond audit append; complete mediation and bypass testing; stronger OS isolation; independently checkpointed evidence; deployment-level conformance; fuzzing/load/penetration testing; independent security review.

## Validation boundary

The CI PASS applies to the exact tested broker head and workflow. It does not certify a production deployment, prove all application side effects are mediated, or establish safety. The broker is Linux-only and trusts the host kernel, broker account, and operator-managed configuration/state.
