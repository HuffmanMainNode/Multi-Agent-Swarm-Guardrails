# Mandatory Safety Contracts

Normative machine-readable index: ../contracts/manifest.json. Contract identifiers are stable; normative changes require versioning and migration notes.

- **MSC-001 Policy Integrity:** bind protected decisions to identified, integrity-checked policy. Current evaluator does not authenticate policy origin.
- **MSC-002 Capability Authorization:** exact principal/action/target/scope authorization. Current evaluator does not authenticate principal.
- **MSC-003 Enforcement Mediation:** every protected side-effect path traverses enforcement. Requires deployment path inventory and bypass tests; not proven by library.
- **MSC-004 Fail-Closed Decision:** invalid, unknown, expired, or unavailable inputs never authorize. Partially demonstrated in reference evaluator.
- **MSC-005 Provenance and Authority Separation:** untrusted content cannot create authority. Requires adopter information-flow controls.
- **MSC-006 Identity and Revocation:** independently authenticate and check revocation freshness. Not implemented.
- **MSC-007 Delegation Attenuation:** delegated authority cannot exceed parent authority. Current cycle check is not attenuation.
- **MSC-008 Evidence Integrity:** verify ordering/integrity under declared storage assumptions. Local hash chain is not tamper-proof.
- **MSC-009 Recovery Integrity:** data restore does not restore trust automatically. Specification only.
- **MSC-010 Responsible Capability:** deny/restrict/review high-risk capabilities. Evaluator supports deny and review effects; no legal classifier.
