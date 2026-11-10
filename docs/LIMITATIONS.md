# Known Limitations

The initial reference release is experimental. It is not a production security boundary and must not be the only control for high-impact actions.

## Implemented reference behavior
- Strict local JSON input parsing rejects duplicate object keys, non-standard numeric constants, unknown fields, malformed selectors, excessive input sizes, and malformed time values.
- Policy decisions are deny-by-default and exact-match. Explicit DENY dominates ALLOW.
- Optional SQLite replay protection atomically consumes request IDs once within one local database.
- The local JSONL evidence ledger verifies its hash chain and rejects ambiguous JSON records.

## Not implemented
- External identity authentication, credential issuance, revocation, or proof of principal ownership.
- Cryptographically authenticated policy distribution or trusted policy rollback prevention.
- Distributed replay protection, database anti-rollback, or replay protection when the optional SQLite store is not configured.
- Capability-set delegation attenuation. Current delegation checks only reject malformed/cyclic chains.
- Independent guardian, protected execution broker, OS sandbox, egress firewall, or complete mediation proof.
- Signed evidence, remote immutable checkpoint, trusted timestamp, or multi-writer-safe JSONL ledger.
- Human approval binding, semantic prompt-injection engine, legality classifier, recovery orchestration, framework adapters, fuzz/load/penetration testing, or independent security assessment.

## Replay-store semantics
Use `masg evaluate --replay-db PATH` to enable local one-time request-ID consumption. A successful decision is committed to SQLite before the evaluator returns ALLOW. A repeated ID is denied. Concurrent consumers serialize through a SQLite write transaction. A storage error fails closed.

This local store is not a distributed replay service. An attacker able to replace, restore, or roll back the database can defeat its history. Protect it with operating-system permissions, backups, and an independently managed rollback-resistant checkpoint where the deployment threat model requires one. An integrator must consume the request ID before performing the side effect and must not execute if the store is unavailable. A crash after consumption but before execution causes a safe availability failure: the ID remains consumed.

## Audit ledger semantics
The JSONL ledger is single-writer only. It has no inter-process locking, fsync durability guarantee, trusted external checkpoint, or protection from whole-file replacement by an attacker who controls the file and checkpoint. Do not use it as a tamper-proof audit service.

## Clock assumptions
The evaluator requires timezone-aware RFC3339 request timestamps and an aware evaluation clock. It does not authenticate time or protect against a compromised system clock. Deployments requiring trusted time must provide it independently.

## Assurance
The structural verifier checks repository artifacts only. Unit tests exercise reference functions, not deployed enforcement paths. No certification, production readiness, complete mediation, or independent audit is claimed.
