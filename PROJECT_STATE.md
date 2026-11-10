# Project State

Checkpoint: 2026-11-10
Repository: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails
Owner: HuffmanMainNode
Creator attribution: MrCakes931
License: Apache-2.0

## Objective
Public, portable, independently verifiable safety substrate for autonomous agents and swarms. Not a hosted service or centralized command center.

## Current milestone
Foundation and input/replay hardening merged in PRs #1-#3; independent Linux broker in PR #4; TUF policy verification in PR #6; SPIFFE JWT-SVID validation in PR #8; language-neutral protocol v1.0.0 in PR #10; Go reference in PR #12; namespaced extension model in PR #13; cross-language semantic parity in PR #16.

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

## Independent Go implementation milestone

PR #12: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/pull/12
Merged commit: 5bab815c412326576b57dd1f3e00317f5fd51489
Go implementation: implementations/go/
Protocol: MASG v1.0.0
Tested Go source revision: 6c43c0f997d627f77f297b2639e34fadd321c407
Go/PR CI run: 42748095348 passed Go vet, Go race tests, and Python 3.11/3.12/3.13.
Final PR CI run after report update: 42748191713 passed all jobs.
Post-merge main CI: 42748296088 passed all jobs.

The independent Go evaluator uses only the Go standard library and consumes the same portable decision vectors as Python. It implements strict JSON parsing (including duplicate-key and invalid UTF-8 rejection), exact selector matching, deny-by-default, explicit deny precedence, review-required, UUIDv4 syntax, RFC3339 expiry, and exact policy-version binding. Its initial five-vector report was expanded to eight policy-decision and request-time vectors in PR #15, then aligned to the full request envelope and strict parser limits in PR #16. Current Go manifest version is 0.1.1; its PASS remains limited to the eight portable vectors in the embedded profile.

It does NOT authenticate the principal, provide a broker/executor, replay database, TUF policy verification, SPIFFE/mTLS, sandbox, OS mediation, evidence ledger, recovery, or complete mediation. All ten MSC contract statuses remain NOT_TESTED in its implementation manifest. This is a second-language protocol proof, not a second complete security system.

## Namespaced extension model milestone

PR #13: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/pull/13
Merged commit: 6b2d94934665ac79f064ddaebd01a8d83f2833ce
PR CI run: 42748658577 passed Python 3.11/3.12/3.13 and Go tests.
Post-merge main CI: 42748737524 passed.

Added a namespaced extension manifest schema, extension package rules, types for domain/transport/identity/policy/enforcement/evidence/recovery adapters, compatibility and fail-closed rules, and a generic tool-action mapping example. The example is metadata/documentation only; no actual MCP/A2A adapter or executable tool adapter is implemented. Extensions cannot weaken core invariants or inject arbitrary fields into v1.0.0 envelopes. Independent communities can host extensions without a central MASG registry or hosted service.

## Next critical engineering priorities

1. Turn the extension model into usable developer tooling: offline manifest validation, compatibility checks, dependency resolution, and extension-specific conformance reports. Keep extension discovery decentralized and publisher trust separate from namespace claims.
2. Build one real transport extension (MCP is the first candidate) with strict tool identity mapping, authenticated principal derivation, stable target/action/scope mapping, refusal on lossy mapping, and bypass tests. Do not claim a generic MCP integration until the actual adapter exists.
3. Close the sender-constrained identity gap: X.509-SVID/mTLS, live SPIRE integration, rotation, revocation propagation, and workload-selector tests.
4. Expand the typed protected executor and complete-mediation tests only after each operation has a fixed schema, independent identity mapping, bounded inputs/resources, evidence, and alternate-path denial tests.
5. Define signed protocol/policy envelopes only after selecting a reviewed canonicalization/signature profile, key discovery/rotation/revocation rules, anti-rollback behavior, and portable cryptographic vectors.

No implementation may claim production readiness or full MSC conformance based only on decision vectors. Keep unsupported capabilities and untested assumptions visible.

## Cross-language semantic parity milestone (PR #16)

PR: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/pull/16
Branch: `protocol/cross-language-semantic-parity`
Tested head: `1b95c53aefd366f5364417b5bdfc6f07b78b95a8`
CI run: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42750849476
CI result: PASS (Python 3.11, 3.12, 3.13; Go vet; Go race tests).\nMerged: `019cd466583779fe38441ef5e62be32e5b1cc191`.\nPost-merge main CI: `42751069709` passed all four jobs.

The Python vector harness now evaluates the complete v1.0.0 request envelope through `evaluate_protocol`; untrusted serialized JSON can use `evaluate_protocol_json` to enforce duplicate-key, UTF-8, constant, nesting and byte-size rules. Go's `EvaluateJSON` performs the equivalent raw-document checks. Both implementations align with the normative schema for required rule IDs, rule/selector counts, field-specific string limits, Unicode code-point counting, optional provenance references, timestamp precision and known-offset requirements.

The eight shared vectors cover exact ALLOW, default DENY, explicit DENY precedence, REVIEW_REQUIRED, policy-version mismatch, expired, not-yet-valid and invalid validity window. Additional CI tests cover schema boundaries, Unicode, duplicate keys, invalid UTF-8, unknown fields, oversized inputs and exact JSON depth boundary.

Scope remains narrow: this establishes protocol parsing and policy-decision interoperability between two implementations. It does not authenticate identity, provide universal execution mediation, prove isolation, or certify deployments. PR #16 merged as `019cd466583779fe38441ef5e62be32e5b1cc191`; post-merge main CI run 42751069709 passed all four jobs.


## Current main checkpoint

Main commit: `019cd466583779fe38441ef5e62be32e5b1cc191`
Post-merge main CI: `42751069709` PASS (Python 3.11/3.12/3.13 and Go).
Open PR #16: none; merged successfully.
Current protocol: MASG v1.0.0.
Current independent implementations: Python reference, Go 0.1.1, and Rust 0.1.0 (Rust PR #18 awaiting merge).
Current shared vectors: eight policy-decision and request-time cases.


## Independent Rust implementation in progress

Branch: `implementations/rust-reference`
Scope: dependency-free Rust parser/evaluator for MASG v1.0.0; same eight shared decision/time vectors; strict UTF-8, duplicate-key, unknown-field, nesting and byte-size handling.
Status: source and CI workflow prepared; Rust compiler is not available in the local editing environment. No conformance result is claimed until the GitHub Rust job passes. The conformance report is deliberately UNKNOWN.


## Independent Rust implementation milestone (PR #18)

PR: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/pull/18
Branch: `implementations/rust-reference`
Tested source revision: `0cc0a0ac4baa906f3757c970f8d881f1ec365ca5`
CI run: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42752336251
CI result: PASS across Python 3.11/3.12/3.13, Go vet/race tests, Rust formatting, Rust Clippy with warnings denied, and Rust tests.

Rust is a dependency-free third implementation with a custom bounded JSON parser. It consumes all eight shared v1.0.0 decision/time vectors and adds parser, Unicode, timestamp, and boundary tests. Its conformance report is PASS only for those eight vectors. All ten MSC statuses remain NOT_TESTED; Rust does not authenticate identity or mediate side effects. PR #18 merge status remains pending.


## Superseding checkpoint: three-language protocol baseline

Current main commit at checkpoint: `2b3aa05450b09d7ba00c79671a0c261a4ec773bd`
Latest main CI: run `42752581046`, PASS (Python 3.11/3.12/3.13, Go vet/race, Rust fmt/Clippy/tests).
Protocol: MASG v1.0.0.
Implementations: Python reference, Go 0.1.1, Rust 0.1.0.
Shared vectors: eight policy-decision and request-time vectors.
Merged Rust milestone: PR #18, merge commit `2b3aa05450b09d7ba00c79671a0c261a4ec773bd`.

This supersedes the earlier text in this file stating Rust PR #18 was pending or that Rust CI had not yet run. Rust's conformance PASS is limited to the eight shared vectors in the embedded profile. The Go report is similarly limited. Both manifests correctly retain NOT_TESTED for all ten mandatory safety contracts. Neither implementation authenticates principals, brokers protected execution, proves complete mediation, or establishes production readiness.

The Python CI suite now validates the Go and Rust implementation manifests and conformance reports against the normative schemas, checks matching implementation IDs/versions/protocol versions, checks the declared eight-vector scope, and requires explicit PASS results, source revision identifiers, evidence links, and visible limitations.

Next quality gate: broaden portable conformance beyond eight policy/time cases, add shared parser-negative fixtures, and run independent differential/property/fuzz testing. Then prioritize the MCP transport adapter only with explicit identity mapping and bypass tests. Keep X.509-SVID/mTLS, live SPIRE, TUF publisher workflow/cache anti-rollback, delegation attenuation, typed executor, complete mediation, recovery, and external security review as open critical work.


## Shared parser-negative conformance milestone (in progress)

Branch: `conformance/shared-parser-negative-vectors`
Protocol: MASG v1.0.0.
Added ten language-neutral raw parser-negative fixtures encoded as hexadecimal bytes. Cases include duplicate keys in policy/request, invalid UTF-8, non-standard NaN, unknown fields, non-object roots, trailing data, excessive nesting and oversized request bodies. The same fixtures are executed by Python, Go, and Rust, with fail-closed decision and reason-code assertions. CI is pending; no parser-negative conformance claim until all three implementation jobs pass.


## Shared parser-negative conformance milestone (merged)

PR #20: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/pull/20
Merge commit: `31f3c9d1f60bf71363250965a2db32d811cd9d3d`
Tested source revision: `283bc384f3c5a9f00e67289ed543282a2906b51b`
PR CI: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42761090847 (PASS)
Post-merge main CI: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42761152825 (PASS)

Added ten shared raw-parser negative fixtures in `vectors/v1.0.0/parser-negative-vectors.json`, represented as hex-encoded byte documents so malformed UTF-8 and duplicate keys are testable. Python, Go, and Rust consume the same fixtures and must return DENY with the exact expected failure reason. Covered: duplicate policy key, duplicate request key, invalid UTF-8, non-standard NaN, unknown request field, non-object request root, trailing data, excessive nesting, oversized request, and unknown policy field.

Rust CI initially caught formatting and Clippy warnings in the new test helper; both were corrected and re-run. The final PR CI passed Python 3.11/3.12/3.13, Go vet/race, Rust fmt/Clippy/tests. Post-merge main CI passed all five jobs. The first two failed CI runs are retained as development history, not counted as passing evidence.

Scope: ten deterministic parser-negative regressions. They are not exhaustive fuzzing, parser memory-safety proof, hostile-load resilience, identity conformance, runtime mediation, or deployment certification. Go/Rust conformance reports remain scoped to the eight positive policy/time vectors; parser-negative regression results are separate CI evidence. All ten MSC statuses remain NOT_TESTED for both independent implementations.

Next quality gate: differential/property testing and fuzzing across the three evaluators; then a Node/TypeScript reference adapter and a portable offline conformance runner. Keep the identity, enforcement, recovery, and supply-chain gaps open.


## JavaScript reference implementation (under review)

Branch: `implementations/javascript-reference`
Node.js 22+, dependency-free ES module with TypeScript declaration file. Intended to consume the same eight decision/time vectors and ten parser-negative fixtures as Python, Go, and Rust. Implements a bounded strict JSON parser, duplicate-key rejection, UTF-8 validation, field/selector bounds, UUIDv4, RFC3339 time checks, and exact-match deny-by-default decisions. CI and conformance report remain pending; do not count it as a supported implementation until tests pass.


## Independent JavaScript implementation milestone

Branch: `implementations/javascript-reference`
Implementation: `implementations/javascript/`, package `@masg/reference-javascript` 0.1.0.
Tested source revision: `e09527b28b28198b1f7a41a055f3a45dd1ac7a5b`
CI run: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42761807335
CI result: PASS for Node.js 22, Python 3.11/3.12/3.13, Go vet/race, Rust fmt/Clippy/tests.

JavaScript is the fourth independent implementation. It is dependency-free, uses a bounded strict JSON parser, provides TypeScript declarations, and passes the same eight policy/time vectors and ten shared parser-negative fixtures. Its conformance report is PASS only for the eight policy/time vectors in the embedded profile. All ten MSC statuses remain NOT_TESTED. The caller supplies the principal and Date clock; neither is authenticated. It does not mediate protected side effects, provide replay, identity, sandbox, evidence, or recovery services.

The implementation is tested but not yet merged. Do not count it as part of main until PR #22 is merged and post-merge CI passes.


## Universal language and AI semantic interoperability checkpoint

- PR #22 merged: independent JavaScript 0.1.0 reference evaluator with TypeScript declarations, Node.js 22 CI, strict bounded JSON parsing, and shared v1.0.0 vectors/parser-negative fixtures. Merge commit: `a6aa2677636a640d9c0f23280a87124a7401eed1`. Six final CI checks passed.
- Four independent language implementations now exist: Python, Go, Rust, and JavaScript. The normative protocol remains language-neutral; no hosted MASG service is required.
- A calendar-validation regression was added to the JavaScript evaluator to reject impossible RFC 3339 dates/times rather than accepting JavaScript date normalization.
- The next update introduces BCP 47 localization packs, stable concept IDs, a human-review workflow, and an experimental UASR semantic-frame proposal. English is the source locale; Spanish is an untranslated template only.
- UASR is not part of authorization protocol v1.0.0. It does not expose hidden model reasoning, authenticate identity, authorize actions, or prove truth.
- Deterministic CBOR is a candidate encoding only. No custom binary language or token-efficiency claim is standardized.


## Localization runtime checkpoint

A follow-on implementation adds offline translation resolvers in Python and JavaScript/TypeScript. Both default to HUMAN_REVIEWED entries, fall back to English for missing, untranslated, or NEEDS_REVISION strings, and require explicit opt-in for MACHINE_DRAFT text. The resolver does not translate content or contact external services. Go/Rust resolvers and full BCP 47 registry validation remain future work.
