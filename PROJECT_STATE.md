# Project State

Checkpoint: 2026-11-10
Repository: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails
Owner: HuffmanMainNode
Creator attribution: MrCakes931
License: Apache-2.0

## Objective
Public, portable, independently verifiable safety substrate for autonomous agents and swarms. Not a hosted service or centralized command center.

## Current milestone
Initial foundation merged in PR #1. Input/replay hardening merged in PR #2. Adversarial review records merged in PR #3.

## Critical engineering milestone: independent broker
PR #4: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/pull/4
Branch: security/independent-linux-execution-broker
Tested head: 6885d489f8aa971c5d409c8de5753a539ef540e5
Status: merged in PR #4. Merge commit: 1c0295204258a4a92315a9e97dba95a33e8202c4. Main-branch CI run 42736182162 passed.

Adds an experimental Linux-only separate-process broker for exactly one fixed operation: audit.append. It derives caller UID using SO_PEERCRED, maps UID to an operator-configured principal, does not accept client-supplied identity or operation fields, applies deny-by-default policy, limits request TTL to five minutes, requires canonical UUIDv4 request IDs, consumes a request ID in SQLite, and appends bounded event data to a broker-owned ledger.

The broker rejects symlink/special config files and group/world-writable config, state, and socket parent directories. It bounds request size, JSON depth, event size, socket read time, and concurrent handler count.

## Validation evidence
Two successful CI runs on the tested head:
- 42735881467
- 42735881291

All Python 3.11, 3.12, and 3.13 jobs passed. Each ran 46 unit tests, package installation, structural verification, and JSON syntax checks. The first broker CI run failed two new validation tests; parser depth and UUID validation were corrected before the successful runs. Details are in docs/STRESS_TEST_RESULTS.md.

## Optional TUF policy source
The broker can load a policy target from a local TUF mirror using python-tuf. The bootstrap root is supplied out-of-band, and the metadata cache persists under an operator-controlled directory. TUF signature, version, expiry, snapshot, and target hash checks must pass before the policy is loaded. Static policy mode remains available but is not publisher-authenticated. MASG does not publish TUF repositories or manage private signing keys. The cache can still be rolled back by an attacker who can restore older cache state.

## TUF validation evidence
PR #6 merged as `e8a8d1400a601ef4277ed388337f630c06531cf2`; branch `security/tuf-policy-trust-and-rollback`, tested head `ba950ae7a69ffe77202d786623fdefb662ae1cd1`. CI runs 42737352852 and 42737349896 passed all Python 3.11, 3.12, and 3.13 jobs; main-branch CI run 42737605525 also passed. Each ran 57 tests plus Ruff, structural verification, and JSON checks. Tests include signed target acceptance, target and metadata tampering, timestamp rollback, expired metadata, wrong bootstrap root, path traversal, unsafe cache permissions, broker startup from verified policy, and fail-closed tamper behavior.

## SPIFFE Workload API integration (merged experimental milestone)
PR #8: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/pull/8
Branch: `security/spiffe-workload-identity`
Tested head: `bb482dcefc1184350b76122ea9bc33c56e35d98c`
Merged: `afac8e19a9d979158ec048c4261a5a993dce39e5`
PR CI: `42744847753`
Post-merge main CI: `42744955882`

Adds an optional SPIFFE mode for the Linux broker. The client presents a bounded JWT-SVID; the broker validates it on every request through the local Workload API's `ValidateJWTSVID` method for an operator-configured exact audience. The validated SPIFFE ID becomes the exact policy principal, and the request expiry cannot outlive the SVID. Legacy UID-map mode remains available and the two modes are mutually exclusive. No positive identity cache or unsigned/offline fallback exists. Tokens are not written to evidence. Endpoint socket path validation rejects symlinks, unsafe writable ancestors and path traversal.

All three Python versions (3.11, 3.12, 3.13) passed 75 tests each, Ruff, package installation, structural verification, and JSON checks on the PR run and post-merge main run. Tests use an injected fake Workload API client. They do not prove live SPIRE interoperability or revocation propagation.

The optional `spiffe` extra pins community-maintained py-spiffe 0.4.0. PyPI reports no provenance for that release; this is explicitly documented as a supply-chain risk requiring review before sensitive deployment. JWT-SVID remains a bearer credential and is not bound to the Unix peer process. No live SPIRE deployment test or X.509-SVID/mTLS sender binding is claimed.

## Security limitations
Linux only. UID mode still depends on OS peer identity and processes sharing a UID share authority. SPIFFE mode depends on local Workload API trust, SPIRE attestation and key/bundle updates; JWT-SVIDs are bearer tokens. Policy and state require operator-controlled files/directories. Optional TUF mode authenticates policy publisher metadata, but its cache can be rolled back if an attacker controls persistent cache storage. Local replay DB can be rolled back. Only audit append is exposed. No arbitrary tool executor, shell, filesystem proxy, network proxy, X.509-SVID/mTLS binding, TUF repository publishing/key management, rollback-resistant cache storage, general sandbox, complete mediation proof, fuzz campaign, penetration test, live SPIRE test, or independent review.

## Next
Complete live SPIRE interoperability, rotation/revocation and workload-selector tests; add sender-constrained X.509-SVID/mTLS; review and improve the optional SDK's supply-chain provenance. Then prioritize TUF repository publishing/signing, stronger rollback-resistant cache storage, capability delegation attenuation, and a typed protected executor. Do not expand broker capabilities until each new operation has a fixed schema, explicit authority mapping, bounded inputs/resources, side-effect evidence, and bypass tests.

## Universal language-neutral protocol milestone

PR #10: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/pull/10
Merged: c595bd6293634b5f7349cf19f45ff44d42a98f20
Protocol version: 1.0.0
Tested PR head: a4fd0c71add091ba2ecd415b6ca3c283029b9eff
PR CI run: 42746824887 (Python 3.11, 3.12, 3.13 all passed)
Post-merge main CI: 42746893640 and 42746898736 both passed.

The normative protocol is now separate from the Python reference package. Added language-neutral JSON Schemas for decision policy, request/response envelopes, implementation manifests, conformance reports and conformance vectors. Added portable v1.0.0 decision vectors for exact allow, default deny, explicit deny precedence, review-required and policy-version mismatch. The Python reference evaluator checks a supplied policy_version against the loaded policy and fails closed on mismatch. The protocol request schema requires policy_version.

Independent implementations may use Rust, Go, Java, C#, JavaScript/TypeScript or any other language/runtime. They do not need Python, the MASG package, a MASG-hosted service, or the same transport. The specification defines normative semantics; adapters and SDKs are replaceable.

Important scope: the first version standardizes policy/decision semantics and conformance artifacts, not a universal execution broker, transport, identity provider, cryptographic signature format, sandbox, or orchestration protocol. The Linux broker remains Linux-only and only supports audit.append. Signed envelopes and canonical JSON signatures are not defined. Full deployment conformance and security assurance remain future work.
