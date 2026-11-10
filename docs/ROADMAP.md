# Roadmap

Priorities are ordered by security dependency, not feature count.

## Experimental foundation
- [x] Ten versioned mandatory safety contracts.
- [x] Deny-by-default local policy evaluator.
- [x] Optional local SQLite replay consumption.
- [x] Local hash-chain evidence ledger.
- [x] Repository structural verifier and CI.
- [x] Experimental Linux separate-process broker for one fixed audit append operation.

## Critical engineering
1. [x] Optional SPIFFE JWT-SVID validation through local Workload API merged in PR #8. Remaining: live SPIRE interoperability/rotation/revocation tests and sender-constrained X.509-SVID/mTLS.
2. [x] Optional TUF policy client verifies signatures, metadata versions/expiry, snapshots, and target hashes from a local mirror. Remaining: repository publishing/signing workflow and independently protected rollback-resistant cache.
3. Cryptographically bound capability delegation with strict attenuation.
4. Typed protected-executor interface and explicit capability registry; no arbitrary shell execution.
5. Expand broker operation-by-operation only after threat model, allowlist, resource limits, authorization, evidence, and bypass tests exist.
6. Independent evidence checkpoint and signed portable evidence format.
7. Deployment-level conformance, property-based/fuzz testing, load testing, and external review.

## Universal protocol and language interoperability
- [x] Publish language-neutral MASG v1.0.0 schemas and eight shared policy/time vectors.
- [x] Python reference evaluator.
- [x] Independent Go standard-library evaluator with race-enabled CI.
- [x] Independent Rust standard-library evaluator with formatting, Clippy and tests.
- [x] Validate Go and Rust implementation manifests/reports against normative schemas in Python CI.
- [ ] Add shared malformed-input/parser-negative fixtures consumed by all implementations.
- [ ] Add cross-language differential/property-based testing and fuzz campaigns.
- [ ] Add JavaScript/TypeScript implementation for common agent/tool ecosystems.
- [ ] Add a portable CLI conformance runner that can validate any implementation report offline.
- [ ] Add a real transport adapter (MCP candidate) only after identity and bypass contracts are defined.

## Interoperability
- ACS/MCP integration only after security contract mappings and compatibility tests.
- A2A identity, audience, expiry, and replay integration.
- OPA/Cedar adapters where they improve interoperability without replacing MASG contracts.

## Release gate
No production or certification claim until identity, policy integrity, execution isolation, complete declared-path mediation, evidence trust, recovery, and independent review are tested in a documented threat model.
