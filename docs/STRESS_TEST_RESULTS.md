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
- No cryptographic workload identity, credential issuance/revocation, signed policy, or policy anti-rollback.
- No distributed replay cache or replay-database anti-rollback test.
- No general arbitrary-tool broker, filesystem/network mediation, or shell/executable execution.
- No multi-process external writer test for the JSONL ledger; broker serializes only its own in-process append handlers.
- No recovery drill, signing-key compromise exercise, real MCP/A2A/ACS interoperability test, or independent assessor review.
- No production safety or certification claim.

## Residual highest-risk gaps

1. OS UID is the broker's caller identity signal. Processes sharing a UID share authority; this is not cryptographic workload identity.
2. Broker service account, host kernel, operator-controlled directories, policy, principal map, replay DB, and ledger remain trusted.
3. SQLite replay state is local and can be rolled back by an attacker controlling broker-owned state. UUIDv4 format does not authenticate the caller or prevent a malicious authorized client from minting fresh IDs.
4. Policy is loaded at startup but is not signed or protected against rollback.
5. Only one fixed operation is brokered. Other application side effects can bypass it unless adopters independently route them through a protected boundary.
6. The JSONL ledger remains replaceable without an independent signed checkpoint.
7. Delegation cycle rejection is not capability attenuation.
8. No independent security review has occurred.

## Acceptance decision

The broker is an experimental reference for one narrow protected operation and passed its current Python CI matrix. It is not a general production security boundary. Adoption requires distinct OS identities, a dedicated broker service account, protected configuration/state/socket directories, and explicit routing of the protected operation through the broker. Do not infer that other side effects are mediated.
