# Multi-Agent Swarm Guardrails (MASG)

**Portable, independently verifiable safety infrastructure for autonomous agents and multi-agent systems.** Created by **MrCakes931**.

MASG is an open-source safety substrate existing systems can clone and integrate without moving their models, prompts, memory, orchestration, data, credentials, or infrastructure into a MASG-operated service.

> No verified authorization, no protected execution.

No hosted control plane, paid API, mandatory telemetry, central registry, or vendor-specific runtime is required.

## Initial implementation
- Ten versioned mandatory safety contract definitions.
- Dependency-free Python reference policy evaluator with strict local input validation and deny-by-default behavior.
- Exact principal/action/target/scope matching, explicit-deny precedence, and request validity checks.
- Optional local SQLite one-time request-ID consumption for replay resistance.
- Local JSONL evidence ledger with a SHA-256 hash chain and verifier.
- Experimental separate-process Linux broker for one fixed protected operation: `audit.append`.
- Broker derives local peer credentials from Linux SO_PEERCRED. Optional SPIFFE mode validates a presented JWT-SVID through the local Workload API for a fixed audience and uses the validated SPIFFE ID as the policy principal; request expiry cannot outlive the SVID. Legacy UID mapping remains available.
- Optional python-tuf 7.x policy verification from an operator-managed local mirror, with out-of-band bootstrap root and persistent metadata cache. CI tests signed-target tampering, metadata tampering, expiry, rollback, and fail-closed broker startup.
- Structural repository conformance CLI, examples, tests, CI, deployment profiles, machine-readable metadata, and security documentation.

## Quick start
Requires Python 3.11+.

```bash
python -m venv .venv
# Linux/macOS: . .venv/bin/activate
# Windows: .venv\\Scripts\\Activate.ps1
python -m pip install -e .  # add [tuf] for TUF policy-source support
masg verify --root .
masg evaluate --policy examples/policy.json --request examples/request.json
python -m unittest discover -s tests -v
```

Without `--replay-db`, replay protection is disabled. With it, an ALLOW consumes the request ID in local SQLite before returning. Repeated IDs are denied. Protect the database from deletion, replacement, and rollback. This is not distributed replay protection.

## Experimental independent broker (Linux only)

The broker is a separate process, not an in-process middleware hook. It collects Linux Unix-domain-socket peer credentials as transport provenance and uses either an operator-configured UID-to-principal map or optional per-request SPIFFE JWT-SVID validation through the local Workload API. It authorizes one fixed operation: appending a bounded event to the broker-owned evidence ledger. The client cannot choose an operation, target, scope, path, executable, or command. In SPIFFE mode the JWT-SVID remains a bearer credential and is not bound to the Unix peer process.

See [docs/INDEPENDENT_BROKER.md](docs/INDEPENDENT_BROKER.md) for broker deployment, [docs/SPIFFE_WORKLOAD_IDENTITY.md](docs/SPIFFE_WORKLOAD_IDENTITY.md) for optional cryptographic workload identity, and [docs/TUF_POLICY_TRUST.md](docs/TUF_POLICY_TRUST.md) for policy publisher verification.

This first broker is deliberately narrow. It is not an arbitrary tool executor, a sandbox, or proof that every side effect in an adopting application is mediated. Processes sharing a UID share the same broker identity.

## Mandatory Safety Contracts
| ID | Requirement |
|---|---|
| MSC-001 | Policy Integrity |
| MSC-002 | Capability Authorization |
| MSC-003 | Enforcement Mediation |
| MSC-004 | Fail-Closed Decision |
| MSC-005 | Provenance and Authority Separation |
| MSC-006 | Identity and Revocation |
| MSC-007 | Delegation Attenuation |
| MSC-008 | Evidence Integrity |
| MSC-009 | Recovery Integrity |
| MSC-010 | Responsible Capability |

Normative catalog: [contracts/manifest.json](contracts/manifest.json). Details: [docs/CONTRACTS.md](docs/CONTRACTS.md).

## Architecture
Agent application -> protocol adapter -> authenticated identity and policy -> MASG enforcement adapter -> protected executor -> independent evidence sink.

A model output is a request, never an authorization token. A signature proves key possession under cryptographic assumptions, not trust, permission, or safety. Multiple agents agreeing is not independent verification when they share a model, key, operator, infrastructure, or data lineage.

## Decision outcomes
The evaluator currently emits ALLOW, REVIEW_REQUIRED, or DENY. Unknown, malformed, expired, or unmatched requests do not receive ALLOW. ALLOW_RESTRICTED and SAFE_STOP are documented dispositions, not implemented evaluator outcomes.

## Important security limitations
This is an experimental reference implementation, not a certified security product:
- Principal strings in the local evaluator are assertions, not authenticated identities.
- Legacy broker mode uses the local OS UID. Optional SPIFFE mode validates bearer JWT-SVIDs online, but does not bind them to the Unix-socket peer process.
- Static policy-file mode is not publisher-authenticated. Optional TUF mode verifies policy metadata and target signatures/hashes; its cache must be protected from rollback.
- SQLite replay protection is local; a database rollback can reset its history.
- Delegation cycle checks are not capability attenuation.
- A local hash chain cannot prevent whole-file replacement by an attacker controlling the file and checkpoint.
- The structural verifier does not test a live deployment or prove complete enforcement mediation.
- The broker supports Linux only and exposes one fixed audit append operation.
- Python in-process code cannot isolate a hostile process controlling the same interpreter.
- No MCP, A2A, ACS, OPA, Cedar, X.509-SVID/mTLS, or OS sandbox adapter is implemented. MASG does not provide a TUF repository publisher or manage signing keys.

Read [docs/UNIVERSAL_PROTOCOL.md](docs/UNIVERSAL_PROTOCOL.md), [SECURITY.md](SECURITY.md), [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md), [docs/SECURITY_BOUNDARIES.md](docs/SECURITY_BOUNDARIES.md), and [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Universal protocol and language implementations

MASG's normative protocol is language-neutral. Python is the first reference implementation, not a required runtime. The versioned specification, JSON Schemas, portable decision vectors, and implementation guide are in [spec/](spec/README.md), [schemas/](schemas/), [vectors/](vectors/), and [docs/IMPLEMENTING_IN_ANY_LANGUAGE.md](docs/IMPLEMENTING_IN_ANY_LANGUAGE.md). Independent Rust, Go, Java, C#, JavaScript/TypeScript, and future implementations can consume the same contracts and test vectors without depending on the Python package.

A first standalone Go evaluator is now available under [implementations/go/](implementations/go/README.md). It consumes the shared v1.0.0 vectors without Python or third-party Go modules. Its PASS is limited to portable policy-decision vectors in the embedded profile; it does not authenticate identities or mediate execution. Rust, Java, C#, and JavaScript/TypeScript implementations have not yet been added.

A conformance PASS applies only to the implementation, version, profile, tests, and environment reported. It is not certification or proof of production security.

## Namespaced extensions

Anyone can adapt MASG for a domain, transport, identity provider, policy engine, enforcement runtime, evidence sink, or recovery system through separately versioned extensions. The core security invariants cannot be weakened. See [the extension model](docs/EXTENSION_MODEL.md) and the [example extension](extensions/examples/generic-tool-action/README.md). The example is documentation only, not a working MCP/tool adapter or automatic trust listing.

## Interoperability
MASG intends to integrate rather than replace mature identity, policy, protocol, sandbox, observability, and supply-chain systems. Integration targets and actual status are listed in [docs/INTEROPERABILITY.md](docs/INTEROPERABILITY.md).

## Attribution
Please retain repository origin and applicable copyright/license notices. Apache-2.0 does not mandate prominent marketing credit; accurate attribution is requested as a community practice. Citation metadata: [CITATION.cff](CITATION.cff).

## License
Apache License 2.0. See [LICENSE](LICENSE).
