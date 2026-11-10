# Engineering Register

Last updated: 2026-11-10

| Area | Status | Evidence and limitation |
|---|---|---|
| Ten mandatory contracts | Specified | Machine-readable catalog; only a subset of requirements is executable |
| Strict policy/request parsing | Implemented in reference evaluator | Duplicate keys, non-standard constants, unknown fields, malformed selectors, and oversized inputs rejected |
| Policy evaluator | Experimental reference implementation | Deny-by-default, exact selectors, explicit deny precedence, expiry checks |
| Identity/revocation | Partial local identity signal | Broker derives Linux peer UID; not cryptographic workload identity, UID sharing collapses principals |
| Replay resistance | Local reference control | SQLite atomic one-time request-ID consumption; rollback/fresh fabricated IDs remain possible |
| Evidence ledger | Experimental local format | SHA-256 chain; broker serializes its appends; no independent checkpoint or anti-rollback |
| Structural verifier | Implemented | Checks repository structure/catalog shape; does not verify deployments |
| Independent execution broker | Experimental, Linux only | Separate process, SO_PEERCRED UID mapping, fixed audit.append allowlist, 5-minute request TTL, bounded inputs, 32 handler limit |
| Broker isolation | Deployment-dependent | Requires distinct UIDs, operator-controlled socket directory/config, dedicated service account and protected state |
| General tool mediation | Not implemented | No arbitrary tool, filesystem, network, shell, or executable execution |
| Unit tests | Pending CI | Broker-specific adversarial tests added; do not report pass until workflow completes |
| Independent review | Not performed | No certification or external audit claim |

## Critical gaps

Cryptographic workload identity and revocation; signed policy provenance and anti-rollback; authenticated request IDs and distributed anti-replay; capability-set delegation attenuation; general protected executor; complete mediation and bypass testing; OS isolation; independently checkpointed evidence; deployment-level conformance; fuzzing/load/penetration testing; independent security review.

## Validation boundary

The previous CI PASS applies to the earlier tested commit, not the newly added broker. The broker must pass the new CI matrix before merge. Unit tests do not certify deployment security or prove all application side effects use the broker.
