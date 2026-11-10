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

## Interoperability
- ACS/MCP integration only after security contract mappings and compatibility tests.
- A2A identity, audience, expiry, and replay integration.
- OPA/Cedar adapters where they improve interoperability without replacing MASG contracts.

## Release gate
No production or certification claim until identity, policy integrity, execution isolation, complete declared-path mediation, evidence trust, recovery, and independent review are tested in a documented threat model.
