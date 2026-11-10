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
- Broker derives caller UID from Linux SO_PEERCRED, maps it to a configured principal, rejects caller-supplied identity/operation, requires canonical UUIDv4 request IDs, consumes them before execution, and writes to its own bounded evidence ledger.
- Structural repository conformance CLI, examples, tests, CI, deployment profiles, machine-readable metadata, and security documentation.

## Quick start
Requires Python 3.11+.

```bash
python -m venv .venv
# Linux/macOS: . .venv/bin/activate
# Windows: .venv\\Scripts\\Activate.ps1
python -m pip install -e .
masg verify --root .
masg evaluate --policy examples/policy.json --request examples/request.json
python -m unittest discover -s tests -v
```

Without `--replay-db`, replay protection is disabled. With it, an ALLOW consumes the request ID in local SQLite before returning. Repeated IDs are denied. Protect the database from deletion, replacement, and rollback. This is not distributed replay protection.

## Experimental independent broker (Linux only)

The broker is a separate process, not an in-process middleware hook. It uses Linux Unix-domain-socket peer credentials to derive the caller UID, maps that UID to an operator-configured principal, and authorizes one fixed operation: appending a bounded event to the broker-owned evidence ledger. The client cannot choose a principal, action, target, scope, path, executable, or command.

See [docs/INDEPENDENT_BROKER.md](docs/INDEPENDENT_BROKER.md) for dedicated service-account setup, UID separation, policy, socket permissions, operation, and residual risks.

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
- The broker's identity signal is the local OS UID, not cryptographic workload identity.
- Policy files are not cryptographically signed or provenance-verified.
- SQLite replay protection is local; a database rollback can reset its history.
- Delegation cycle checks are not capability attenuation.
- A local hash chain cannot prevent whole-file replacement by an attacker controlling the file and checkpoint.
- The structural verifier does not test a live deployment or prove complete enforcement mediation.
- The broker supports Linux only and exposes one fixed audit append operation.
- Python in-process code cannot isolate a hostile process controlling the same interpreter.
- No MCP, A2A, ACS, OPA, Cedar, SPIFFE/SPIRE, or OS sandbox adapter is implemented.

Read [SECURITY.md](SECURITY.md), [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md), [docs/SECURITY_BOUNDARIES.md](docs/SECURITY_BOUNDARIES.md), and [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Interoperability
MASG intends to integrate rather than replace mature identity, policy, protocol, sandbox, observability, and supply-chain systems. Integration targets and actual status are listed in [docs/INTEROPERABILITY.md](docs/INTEROPERABILITY.md).

## Attribution
Please retain repository origin and applicable copyright/license notices. Apache-2.0 does not mandate prominent marketing credit; accurate attribution is requested as a community practice. Citation metadata: [CITATION.cff](CITATION.cff).

## License
Apache License 2.0. See [LICENSE](LICENSE).
