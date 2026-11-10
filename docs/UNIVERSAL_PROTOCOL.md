# Universal, Language-Neutral MASG Architecture

MASG is a protocol and set of safety contracts, not a single-language framework. Python is the first reference implementation; an independent Go policy-decision implementation now consumes the same protocol vectors.

## Separation of concerns

| Layer | Normative or replaceable? | Purpose |
|---|---|---|
| Safety contracts and protocol semantics | Normative | Same meaning across every implementation |
| JSON Schemas and conformance vectors | Normative | Shared machine-readable interface and expected behavior |
| Transport adapters | Replaceable | HTTP, sockets, pipes, gRPC, MCP, A2A, queues, or native IPC |
| Identity providers | Replaceable, policy constrained | SPIFFE/SPIRE, OS identity, mTLS, workload identity, or other verified providers |
| Policy engines | Replaceable behind contract | Native evaluator, OPA, Cedar, or another engine that passes semantic vectors |
| Runtime enforcement | Deployment-specific | Process broker, OS controls, sandbox, hypervisor, hardware, or embedded hooks |
| Language SDKs | Replaceable | Python, Rust, Go, Java, C#, JavaScript/TypeScript, and future languages |

No language SDK is the source of truth. The normative source is `spec/`, `schemas/`, contract catalog, and versioned vectors. Domain and transport adaptations are packaged as independent namespaced extensions under the rules in [docs/EXTENSION_MODEL.md](EXTENSION_MODEL.md).

## Universal does not mean identical deployment

A Python package cannot enforce a Rust process's system calls merely by being imported. An embedded library cannot protect against a hostile host process that controls the same address space. A Linux SO_PEERCRED broker is not portable to Windows or browser runtimes. Hardware-backed claims require hardware-specific attestation and independent verification.

Implementations MUST declare:
- languages, runtimes, operating systems and transport adapters;
- supported protocol and contract versions;
- supported assurance profiles;
- identity source and how principal provenance is established;
- protected side-effect paths and known bypass paths;
- policy source and rollback assumptions;
- replay and evidence storage semantics;
- unavailable controls, unsupported operations and untested conditions.

## Profiles are evidence descriptions

- **Embedded:** in-process library. Host process is trusted; no isolation from a hostile same-process agent.
- **Isolated:** separate process/container with authenticated IPC and independently controlled OS permissions. Must be tested in the actual deployment.
- **Hardware-Assured:** hardware-backed key protection and fresh attestation verified by an independent trust path. A label alone is not evidence.

Profiles are not marketing tiers. A deployment may be isolated for one path and embedded for another; report per protected path where possible.

## Replaceable implementation model

1. Read the normative protocol and contract versions.
2. Select or write an implementation in the preferred language.
3. Implement the same policy semantics and error behavior.
4. Validate against shared schemas.
5. Run all applicable portable vectors.
6. Add runtime-specific adversarial tests for identity, isolation, mediation, replay, recovery and failure modes.
7. Publish an implementation manifest and conformance report, including limitations.
8. Integrate only the capabilities whose evidence is adequate for the deployment threat model.

An implementation may replace the Python reference completely. It does not need to call Python, run MASG's package, or depend on a MASG-operated service.

## Compatibility rule

Implementations are compatible only when they agree on protocol version, policy semantics, decision precedence, identity provenance requirements, timestamp behavior, errors, and conformance vectors. Similar field names are not enough.
