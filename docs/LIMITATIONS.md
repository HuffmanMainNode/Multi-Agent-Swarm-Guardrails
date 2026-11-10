# Known Limitations

The reference implementation is experimental. It is not a production security boundary and must not be the only control for high-impact actions.

## Implemented reference behavior
- Strict local JSON input parsing rejects duplicate object keys, non-standard numeric constants, unknown fields, malformed selectors, excessive input sizes, and malformed time values.
- Policy decisions are deny-by-default and exact-match. Explicit DENY dominates ALLOW.
- Optional SQLite replay protection atomically consumes request IDs once within one local database.
- The local JSONL evidence ledger verifies its hash chain and rejects ambiguous JSON records.
- Experimental Linux broker uses OS peer UID credentials, an operator-maintained UID-to-principal map, one fixed audit append operation, bounded request/event sizes, a five-minute maximum request lifetime, local replay consumption, and a broker-owned evidence ledger.

## Not implemented
- External cryptographic identity authentication, credential issuance, revocation, or proof of principal ownership beyond the local OS UID.
- Cryptographically authenticated policy distribution or trusted policy rollback prevention.
- Distributed replay protection, database anti-rollback, or replay protection when the optional SQLite store is not configured.
- Capability-set delegation attenuation. Current evaluator checks only reject malformed/cyclic chains.
- General arbitrary-tool execution broker, filesystem/network mediation, OS sandbox, egress firewall, or complete mediation proof.
- Signed evidence, remote immutable checkpoint, trusted timestamp, or multi-writer-safe JSONL ledger.
- Human approval binding, semantic prompt-injection engine, legality classifier, recovery orchestration, framework adapters, fuzz/load/penetration testing, or independent security assessment.

## Broker-specific limits
- Linux only; requires SO_PEERCRED and Unix domain sockets.
- Processes sharing an OS UID share the same broker identity.
- Policy and UID map are loaded at startup. Files must be regular and not group/world writable; parent directories still require operator protection.
- Broker socket parent must already exist and be operator-controlled. Existing socket paths are never removed automatically.
- Exactly one operation is exposed: append a bounded event to the broker-owned ledger. No arbitrary commands, paths, executables, or tool names are accepted.
- Replay state is local and can be rolled back by an attacker controlling broker-owned state.
- More than 32 simultaneous connection handlers are dropped. Socket reads have a three-second timeout.
- An append failure after request-ID consumption requires operator inspection; the request ID is not automatically reusable.

## Replay-store semantics
Use `masg evaluate --replay-db PATH` to enable local one-time request-ID consumption. A successful decision is committed to SQLite before the evaluator returns ALLOW. A repeated ID is denied. Concurrent consumers serialize through a SQLite write transaction. A storage error fails closed.

This local store is not a distributed replay service. An attacker able to replace, restore, or roll back the database can defeat its history. Protect it with operating-system permissions, backups, and an independently managed rollback-resistant checkpoint where the deployment threat model requires one. An integrator must consume the request ID before performing the side effect and must not execute if the store is unavailable. A crash after consumption but before execution causes a safe availability failure: the ID remains consumed.

## Audit ledger semantics
The JSONL ledger is single-writer only. The broker serializes its own append calls, but the format has no trusted external checkpoint or protection from whole-file replacement by an attacker who controls the file and checkpoint. Do not use it as a tamper-proof audit service.

## Clock assumptions
The evaluator requires timezone-aware RFC3339 request timestamps and an aware evaluation clock. It does not authenticate time or protect against a compromised system clock. The broker additionally limits request lifetime to five minutes but still relies on the host clock.

## Assurance
The structural verifier checks repository artifacts only. Unit tests exercise reference functions and a local Unix socket, not a deployed service configuration or all side-effect paths. No certification, production readiness, complete mediation, or independent audit is claimed.
