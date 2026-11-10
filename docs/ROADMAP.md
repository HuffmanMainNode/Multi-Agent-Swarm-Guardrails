# Roadmap

Roadmap entries are proposals, not current capabilities.

## Foundation
- [x] Ten stable contract IDs and machine-readable catalog.
- [x] Local reference evaluator, evidence chain, structural CLI, tests, CI.
- [ ] Independent contract and code review.

## Core strengthening
- Strict schema validation.
- Property-based/fuzz testing.
- Durable replay protection with concurrency semantics.
- Capability-set delegation attenuation and signed delegation using maintained libraries.
- Policy provenance/signature profile.
- External evidence checkpointing and concurrency-safe ledger.
- Reproducible package builds and provenance.

## Deployment enforcement
- Isolated enforcement service with authenticated IPC.
- Tool broker and protected executor example.
- Bypass-path test harness.
- Safe-stop interfaces and tested recovery.

## Interoperability
- MCP, A2A, ACS, OPA/Cedar, SPIFFE/SPIRE, OpenTelemetry, CycloneDX/SPDX adapters.

## Independent adoption
- Portable Security Passport with signature profile.
- At least two independent language implementations.
- Cross-implementation test vectors and verifier.
- Community governance and maintainer succession.

A phase is complete only when code exists, tests are executed, evidence retained, limitations documented, and status registers updated.
