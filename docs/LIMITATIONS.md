# Known Limitations

The reference implementation is experimental. It is not a production security boundary and must not be the only control for high-impact actions.

## Implemented reference behavior
- Strict local JSON input parsing rejects duplicate object keys, non-standard numeric constants, unknown fields, malformed selectors, excessive input sizes, and malformed time values.
- Policy decisions are deny-by-default and exact-match. Explicit DENY dominates ALLOW.
- Optional SQLite replay protection atomically consumes request IDs once within one local database.
- The local JSONL evidence ledger verifies its hash chain and rejects ambiguous JSON records.
- Experimental Linux broker supports one fixed audit append operation, bounded requests, a five-minute request lifetime, local replay consumption and a broker-owned evidence ledger. It supports legacy UID principal mapping and an optional experimental SPIFFE JWT-SVID validation mode.

## Not implemented
- Live SPIRE deployment conformance, X.509-SVID/mTLS sender binding, and proof-of-possession for the JWT-SVID bearer token.
- Credential issuance, SPIRE workload registration, key administration, or globally instantaneous revocation. Optional SPIFFE mode validates JWT-SVIDs through the local Workload API on every request; trust provider, workload attestation, key rotation and revocation propagation remain adopter dependencies.
- Static local policy mode has no publisher authentication. Optional TUF mode verifies policy metadata, signatures, expiry, versions, and target hashes through python-tuf; its cache must be persistent and protected against rollback. MASG does not provide TUF repository publishing or signing-key management.
- Distributed replay protection, database anti-rollback, or replay protection when the optional SQLite store is not configured.
- Capability-set delegation attenuation. Current evaluator checks only reject malformed/cyclic chains.
- General arbitrary-tool execution broker, filesystem/network mediation, OS sandbox, egress firewall, or complete mediation proof.
- Signed evidence, remote immutable checkpoint, trusted timestamp, or multi-writer-safe JSONL ledger.
- Human approval binding, semantic prompt-injection engine, legality classifier, recovery orchestration, framework adapters, fuzz/load/penetration testing, or independent security assessment.

## SPIFFE workload identity limits
- Optional `spiffe` extra pins community-maintained py-spiffe 0.4.0; PyPI currently reports no provenance for the release. Audit and hash-pin the dependency closure before sensitive deployment.
- Requires a local SPIFFE Workload API Unix socket and operator-configured audience.
- Every request is validated online; Workload API failure or timeout fails closed. No identity cache or offline fallback exists.
- Request expiry is bounded by the validated SVID expiry.
- Revocation depends on provider trust-bundle/key update propagation. No globally instantaneous revocation guarantee.
- JWT-SVID is a bearer token; theft enables presentation until expiry or provider-side invalidation.
- No X.509-SVID/mTLS sender binding, real SPIRE integration test, or workload selector change test yet.

## TUF policy-source limits
- TUF support is optional and requires the `masg-guardrails[tuf]` extra.
- The adopter must provision a trusted root bootstrap out-of-band and operate a TUF-compatible signing/publishing workflow.
- The repository implements a local-directory mirror fetcher only; it does not host metadata or publish/sign TUF repositories.
- The metadata cache must persist and be protected from agent writes and rollback. Restoring an old cache can undermine rollback detection.
- TUF metadata expiration relies on the host clock; stale or expired metadata fails closed.
- Only one active updater per cache is supported; do not run concurrent brokers against one TUF cache.
- Static `--policy` mode remains available but is not publisher-authenticated.

## Broker-specific limits
- Linux only; requires SO_PEERCRED and Unix domain sockets.
- Processes sharing an OS UID share the same broker identity in UID mode. SPIFFE mode uses the validated SPIFFE ID as policy principal, but presented JWT-SVIDs are bearer tokens not bound to the Unix peer process.
- Policy and UID map are loaded at startup in UID mode. Files must be regular and not group/world writable; parent directories still require operator protection.
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

## Universal protocol limits

- Protocol v1.0.0 standardizes policy/decision envelopes and conformance artifacts; it does not standardize a universal execution transport, arbitrary protected executor, identity provider, sandbox, or orchestration protocol.
- Python, Go 0.1.1, and Rust 0.1.0 reference implementations are included. Go and Rust pass the same eight shared v1.0.0 policy-decision/time vectors and ten shared raw-parser negative fixtures, plus implementation-specific parser/limit regression tests in the embedded profile; neither authenticates principals or mediates side effects. Java, C#, and JavaScript/TypeScript implementations have not yet been added.
- Shared vectors currently cover a small set of policy outcomes. They do not cover all identity, replay, delegation, recovery, runtime mediation, concurrency, distributed, or hardware-assurance behaviors.
- No signed envelope or cross-language canonical JSON signature profile is defined. Do not treat JSON serialization bytes as a stable signature input.
- The namespaced extension model and manifest schema define packaging and compatibility rules, not trust. The example tool-action profile is documentation only; no MCP/A2A adapter, extension publisher authentication, signature verification, or discovery registry is implemented.
- Schema validation and policy-vector agreement do not prove identity provenance, complete mediation, runtime isolation, or production safety.
- Protocol v1.0.0 requires exact policy-version binding in its decision request envelope. The reference evaluator checks the version when supplied; the protocol schema requires it.

## Assurance
The structural verifier checks repository artifacts only. Unit tests exercise reference functions and a local Unix socket, not a deployed service configuration or all side-effect paths. No certification, production readiness, complete mediation, or independent audit is claimed.


## Cross-language protocol limits

Protocol v1.0.0 defines a maximum 1 MiB policy document, 64 KiB request envelope, 1,000 policy rules, and 128 selectors per selector field. Field string limits follow the normative JSON Schemas and count Unicode code points, not UTF-8 bytes. Timestamp strings allow zero to six fractional-second digits and require a known explicit offset; the RFC 3339 unknown-local-offset marker `-00:00` is rejected. The Python and Go protocol entry points are tested against these constraints. The legacy Python evaluator API is a local internal API; protocol consumers should use `evaluate_protocol`.


## Cross-language protocol parser and limits

Protocol v1.0.0 defines a maximum 1 MiB policy document, 64 KiB request envelope, 32 JSON nesting levels, 1,000 policy rules, and 128 selectors per selector field. Field string limits follow the normative JSON Schemas and count Unicode code points, not UTF-8 bytes. Timestamp strings allow zero to six fractional-second digits and require a known explicit offset; the RFC 3339 unknown-local-offset marker `-00:00` is rejected.

The Python protocol entry points are `evaluate_protocol` for an already-parsed complete envelope and `evaluate_protocol_json` for untrusted serialized bytes. The latter rejects duplicate keys, invalid UTF-8, non-standard constants, excessive nesting and oversized inputs. Go's `EvaluateJSON` applies equivalent raw-document checks. Passing these parser tests does not authenticate the principal or prove side-effect mediation.


## Cross-language conformance status

Python and Go currently pass eight shared v1.0.0 decision/time vectors and CI regression tests for schema limits and strict parsing. Python's protocol entry points are `evaluate_protocol` and `evaluate_protocol_json`; Go's are `Evaluate` and `EvaluateJSON`. This is limited evaluator/parser interoperability. No Rust, Java, C#, or TypeScript implementation is included yet. Neither implementation authenticates principal identity on its own or proves complete mediation, deployment isolation, safe side effects, or production readiness.


Rust 0.1.0 is dependency-free and passed formatting, Clippy, shared-vector and parser/limit CI tests. Its report is narrowly scoped to eight vectors. All MSC statuses remain NOT_TESTED; it does not provide identity, replay, broker, sandbox, evidence, recovery or complete mediation.
