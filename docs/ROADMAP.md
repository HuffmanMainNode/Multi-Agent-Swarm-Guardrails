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
1. Authenticated workload identity and revocation integration beyond local OS UID.
2. Signed policy provenance, freshness, and anti-rollback update process.
3. Cryptographically bound capability delegation with strict attenuation.
4. Typed protected-executor interface and explicit capability registry; no arbitrary shell execution.
5. Expand broker operation-by-operation only after threat model, allowlist, resource limits, authorization, evidence, and bypass tests exist.
6. Independent evidence checkpoint and signed portable evidence format.
7. Deployment-level conformance, property-based/fuzz testing, load testing, and external review.

## Interoperability
- ACS/MCP integration only after security contract mappings and compatibility tests.
- A2A identity, audience, expiry, and replay integration.
- OPA/Cedar and SPIFFE/SPIRE adapters where they improve interoperability without replacing MASG contracts.

## Release gate
No production or certification claim until identity, policy integrity, execution isolation, complete declared-path mediation, evidence trust, recovery, and independent review are tested in a documented threat model.
