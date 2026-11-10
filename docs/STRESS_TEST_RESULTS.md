# Adversarial Review and Stress-Test Results

Date: 2026-11-10

## Previous evaluator hardening

Implementation merged in PR #2, merge commit `4a8adac5308e0414018484f68ca4b28d43a053cd`.
CI run: [42734201509](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42734201509).

The second review corrected input ambiguity, weak bounds, local clock handling, missing replay resistance, ledger parsing ambiguity, and shallow contract catalog validation. A ledger newline defect was exposed by CI, corrected, and retested.

Result: 28 unit tests passed on Python 3.11, 3.12, and 3.13, with structural/contract verification and JSON checks passing.

## Independent broker implementation

PR #4: [Independent Linux execution broker](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/pull/4), merged as `1c0295204258a4a92315a9e97dba95a33e8202c4`.
Tested head: `6885d489f8aa971c5d409c8de5753a539ef540e5`.
Main-branch CI after merge: [42736182162](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42736182162), all three jobs passed with 46 tests each.

Successful CI runs:
- [42735881467](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42735881467)
- [42735881291](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42735881291)

All three Python jobs (3.11, 3.12, 3.13) passed in both runs. Each job ran 46 unit tests and completed package installation, structural verification, and JSON syntax checks.

### Broker attack and failure cases exercised

| Test | Expected result | Observed |
|---|---|---|
| Authorized local OS peer with matching policy | Fixed audit append executes | PASS |
| Reuse same UUIDv4 request ID | DENY; no second append | PASS |
| Unmapped OS UID | DENY | PASS |
| Caller supplies principal or shell operation | Reject request shape | PASS |
| Caller adds path or unexpected event field | DENY | PASS |
| Oversized event detail | DENY | PASS |
| Duplicate JSON keys | DENY | PASS |
| Deeply nested JSON | Reject within parser/depth bounds | PASS |
| Non-UUIDv4 request ID | DENY with specific reason | PASS |
| Request validity longer than five minutes | DENY | PASS |
| No matching policy rule | DENY; no ledger write | PASS |
| Replay store unavailable | DENY; no ledger write | PASS |
| Existing corrupt evidence ledger | DENY; no ALLOW | PASS |
| Eight concurrent attempts with one request ID | Exactly one execution | PASS |
| Real Unix socket request/response | Peer UID derived and response returned | PASS |
| Symlink policy file | Broker configuration rejected | PASS |
| Group/world-writable config directory | Broker configuration rejected | PASS |
| Group/world-writable state directory | Broker configuration rejected | PASS |

The socket integration test exercises Linux `SO_PEERCRED`. Most policy/failure tests call the broker's request-processing method with an explicit UID to isolate the relevant condition. They are unit/integration tests, not a deployed multi-user penetration test.

### CI failure and correction record

The first run on the broker branch failed two newly added tests:
1. Deep JSON nesting was not rejected at the intended explicit depth boundary.
2. A malformed request ID was categorized as a generic field error.

The implementation was changed to enforce a maximum JSON nesting depth of 32 and to validate canonical UUIDv4 request IDs before other request fields. The updated matrix passed. Additional tests were then added for symlink configuration and unsafe writable parent directories; the final 46-test-per-version matrix passed.

## Earlier evaluator cases exercised

| Area | Test or attack | Expected result | Observed |
|---|---|---|---|
| Policy | No matching rule | DENY | PASS |
| Policy | Explicit DENY before/after ALLOW | DENY regardless of order | PASS |
| Policy | REVIEW_REQUIRED matching rule | No ALLOW | PASS |
| Policy | Expired/future-issued request | DENY | PASS |
| Policy | Timestamp without timezone or naive clock | DENY | PASS |
| Policy | Unknown request/policy fields | DENY | PASS |
| Policy | Malformed/empty selector | DENY | PASS |
| JSON | Duplicate keys and NaN/Infinity | Reject input | PASS |
| Delegation | Repeated actor/cycle | DENY | PASS |
| Replay | Same request ID across store instances | DENY second use | PASS |
| Replay | Eight concurrent consumers | Exactly one succeeds | PASS |
| Audit | Tamper, blank line, unhashed field, boolean sequence | Invalid ledger | PASS |
| Catalog | Missing/duplicate/unexpected IDs or extra fields | FAIL | PASS |

PASS means the corresponding automated test passed, not that the control is proven against every attacker or deployment.

## Not tested / not claimed

- No penetration test, external red-team engagement, fuzzing campaign, property-based test campaign, or high-volume performance/load benchmark.
- No deployed service-account configuration test or multi-user/multi-host test.
- No live OS sandbox, container escape, network egress, kernel boundary, hardware attestation, or complete-mediation test.
- No live SPIRE deployment/rotation/revocation test, credential issuance/administration, or X.509-SVID/mTLS sender binding. Optional JWT-SVID validation through the local Workload API is covered in the SPIFFE section below.
- No distributed replay cache or replay-database anti-rollback test.
- No general arbitrary-tool broker, filesystem/network mediation, or shell/executable execution.
- No multi-process external writer test for the JSONL ledger; broker serializes only its own in-process append handlers.
- No recovery drill, signing-key compromise exercise, real MCP/A2A/ACS interoperability test, or independent assessor review.
- No production safety or certification claim.

## Residual highest-risk gaps

1. UID mode derives caller principal from OS UID, so processes sharing a UID share authority. SPIFFE mode derives a validated JWT-SVID principal but the bearer token is not bound to the Unix-socket peer.
2. Broker service account, host kernel, operator-controlled directories, policy, principal map, replay DB, and ledger remain trusted.
3. SQLite replay state is local and can be rolled back by an attacker controlling broker-owned state. UUIDv4 format does not authenticate the caller or prevent a malicious authorized client from minting fresh IDs.
4. Policy is loaded at startup but is not signed or protected against rollback.
5. Only one fixed operation is brokered. Other application side effects can bypass it unless adopters independently route them through a protected boundary.
6. The JSONL ledger remains replaceable without an independent signed checkpoint.
7. Delegation cycle rejection is not capability attenuation.
8. No independent security review has occurred.

## Acceptance decision

The broker is an experimental reference for one narrow protected operation and passed its current Python CI matrix. It is not a general production security boundary. UID-mode adoption requires distinct OS identities; SPIFFE-mode adoption requires distinct SPIFFE workload identities and protected Workload API socket access. All modes require a dedicated broker service account, protected configuration/state/socket directories, and explicit routing of the protected operation through the broker. Do not infer that other side effects are mediated.


## TUF-verified policy source

PR #6: [TUF-verified policy updates](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/pull/6), merged as `e8a8d1400a601ef4277ed388337f630c06531cf2`. Tested head: `ba950ae7a69ffe77202d786623fdefb662ae1cd1`.

Successful CI runs:
- [42737352852](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42737352852)
- [42737349896](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42737349896)

Both runs passed all Python 3.11, 3.12, and 3.13 jobs. The post-merge main run [42737605525](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42737605525) also passed all three jobs with 57 tests each. Each job ran 57 tests, Ruff static checks, structural verification, and JSON syntax checks. CI installed python-tuf 7.0.1 and securesystemslib 1.6.0 through the optional TUF extra.

### TUF-specific cases exercised

| Test | Expected result | Observed |
|---|---|---|
| Valid signed policy target | Verify metadata and target, return bytes | PASS |
| Tampered target bytes | Reject target hash/length mismatch | PASS |
| Tampered targets metadata | Reject snapshot metadata hash/length mismatch | PASS |
| Restore older timestamp after accepting newer version | Reject rollback | PASS |
| Expired metadata | Fail closed | PASS |
| Wrong but internally valid bootstrap root | Reject repository signatures | PASS |
| Target path traversal | Reject before fetch | PASS |
| Group/world-writable cache directory | Reject configuration | PASS |
| Broker starts from TUF-verified policy | Load verified target through strict policy parser | PASS |
| Mixed static and TUF policy sources | Reject ambiguous configuration | PASS |
| Tampered TUF target at broker startup | Refuse startup; no unsigned fallback | PASS |

The tests generate ephemeral Ed25519 role keys in temporary directories. No private signing keys are committed. The tests use a local directory mirror and do not require an external TUF service.

### CI failure and correction record

The first TUF CI attempt stopped at Ruff before unit tests. The reported issues were import ordering, the type used for a non-object JSON value, UTC parsing style, and a test import order. These were corrected. The UTC parsing change retains Python 3.11+ behavior, and no unsafe automated Ruff fix was applied. The final 57-test matrix and static checks passed.

### TUF assurance limits

- No repository publisher or signing-key management workflow is implemented by MASG.
- No root-key rotation test, multi-signature threshold test, delegated-role test, or production mirror deployment test is claimed.
- The metadata cache can be rolled back by an attacker who can restore old cache state. Protect it with OS/storage controls or an independent monotonic checkpoint.
- Metadata expiry relies on the host clock.
- The bootstrap root must be provisioned out-of-band; its initial correctness is an adopter responsibility.
- TUF authenticates policy distribution, not the policy's wisdom, legality, safety, or runtime enforcement.


## SPIFFE JWT-SVID workload identity integration

PR #8: [Optional SPIFFE workload identity validation](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/pull/8), merged as `afac8e19a9d979158ec048c4261a5a993dce39e5`. Tested head: `bb482dcefc1184350b76122ea9bc33c56e35d98c`.

CI:
- PR matrix: [42744847753](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42744847753)
- Post-merge main matrix: [42744955882](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42744955882)

Both runs passed Python 3.11, 3.12 and 3.13. Each job ran 75 unit tests, Ruff static checks, package installation including the optional `spiffe` extra, structural verification and JSON syntax checks.

### SPIFFE-specific cases exercised

| Test | Expected result | Observed |
|---|---|---|
| Validated JWT-SVID | Return SPIFFE ID and SVID expiry | PASS |
| Invalid JWT-SVID | Fail closed | PASS |
| Wrong audience | Reject identity | PASS |
| Expired SVID expiry claim | Reject identity | PASS |
| Empty/wildcard/padded audience | Reject configuration | PASS |
| Malformed or oversized token | Reject before Workload API call | PASS |
| Workload API client factory and RPC arguments | Use configured Unix socket, timeout and exact audience | PASS |
| Relative socket path or path containing `..` | Reject configuration | PASS |
| Regular file instead of Unix socket | Reject configuration | PASS |
| Group/world-writable socket parent | Reject configuration | PASS |
| Symlinked socket path component | Reject configuration | PASS |
| Symlinked ancestor directory | Reject configuration | PASS |
| Exact SPIFFE ID in policy | Use validated ID as policy principal | PASS |
| Workload API validation error | DENY; no evidence append | PASS |
| Request expires after SVID | DENY; no evidence append | PASS |
| UID map combined with SPIFFE verifier | Reject ambiguous identity mode | PASS |
| Client supplies a principal field | Reject request shape | PASS |
| Evidence contents | Do not write the JWT-SVID bearer token | PASS |

The Workload API client itself is exercised through an injected fake. The optional SDK is installed and its top-level client factory and call contract are tested, but CI does not connect to a live SPIRE Agent. No live SPIRE key rotation, bundle update/removal, revocation, workload attestation selector, or multi-trust-domain test is claimed.

### CI failure and correction record

The first PR run exposed Ruff findings for broad exception handling and nested context managers. These were corrected by making the broker catch the adapter's explicit fail-closed error type and combining context managers.

The next run exposed a test fixture that attempted to use an ALLOW default policy, which the MASG policy loader correctly rejects. The fixture was changed to DENY by default with an exact SPIFFE-ID ALLOW rule, preserving the project's default-deny invariant.

Additional path-hardening tests then exposed an import-order finding. Imports were sorted and the final 75-test matrix passed. The intermediate CI failures are retained in Actions history; they are not represented as successful runs.

### Integration limits

- The optional dependency is community-maintained py-spiffe 0.4.0, pinned exactly. PyPI reports no publishing provenance for this release; this must be reviewed before sensitive deployment. The transitive dependency closure is not hash-pinned by MASG.
- JWT-SVIDs are bearer tokens. A stolen token may be presented by another process with access to the broker socket until expiry or provider-side invalidation.
- The broker validates every request online through the Workload API and has no identity cache or offline fallback. Provider outage/timeout fails closed.
- Revocation depends on Workload API trust-bundle/key update propagation; no globally instantaneous revocation guarantee.
- Request expiry cannot exceed the validated SVID expiry.
- No X.509-SVID/mTLS sender binding, live SPIRE integration, production deployment, or certification is claimed.
