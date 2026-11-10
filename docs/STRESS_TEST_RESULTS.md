# Adversarial Review and Stress-Test Results

Date: 2026-11-10
Reviewed implementation: PR #2 head aab694b0a58a6ccc741376628498bc9820b88107
Merged commit: 4a8adac5308e0414018484f68ca4b28d43a053cd
CI run: https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42734201509

## Executive result

The second review found and corrected input ambiguity, weak bounds, local clock handling, missing replay resistance, ledger parsing ambiguity, and shallow contract catalog validation. One newly added ledger test initially failed in CI because the record writer emitted a literal backslash-n instead of a line terminator. The failure was investigated from the job log, corrected, and the full matrix rerun. This is recorded rather than hidden.

Final CI result: 28 unit tests passed on each of Python 3.11, 3.12, and 3.13; package installation, structural/contract verification, and JSON syntax checks passed in all three jobs.

## Attack and failure cases exercised

| Area | Test or attack | Expected result | Observed |
|---|---|---|---|
| Policy | No matching rule | DENY | PASS |
| Policy | Explicit DENY before/after ALLOW | DENY regardless of order | PASS |
| Policy | REVIEW_REQUIRED matching rule | No ALLOW | PASS |
| Policy | Expired request | DENY | PASS |
| Policy | Future-issued request | DENY | PASS |
| Policy | Timestamp without timezone | DENY | PASS |
| Policy | Naive evaluator clock | DENY | PASS |
| Policy | Unknown request/policy fields | DENY | PASS |
| Policy | Malformed/empty selector | DENY | PASS |
| JSON | Duplicate policy keys | Reject input | PASS |
| JSON | NaN/Infinity token | Reject input | PASS |
| Delegation | Repeated actor/cycle | DENY | PASS |
| Replay | Reuse same request ID | DENY second use | PASS |
| Replay | New store instance, same DB | Remains consumed | PASS |
| Replay | Eight concurrent consumers | Exactly one succeeds | PASS |
| Replay | Different request IDs | Independent entries | PASS |
| Audit | Modify event content | Detect hash mismatch | PASS |
| Audit | Blank line | Invalid ledger | PASS |
| Audit | Add unhashed field | Invalid ledger | PASS |
| Audit | Boolean sequence value | Invalid ledger | PASS |
| Audit | Duplicate JSON keys | Invalid ledger | PASS |
| Audit | NaN event value | Reject append | PASS |
| Catalog | Missing/duplicate/unexpected contract IDs | FAIL | PASS |
| Catalog | Extra contract field | FAIL | PASS |
| Catalog | Required ten-contract catalog | PASS | PASS |

PASS means the corresponding automated test passed, not that the control is proven against every attacker or deployment.

## Fixes made from findings

1. Strict JSON parsing rejects duplicate object keys and non-standard numeric constants.
2. Policy and request input sizes, rule counts, selector counts, string lengths, and delegation chain length are bounded.
3. Unknown fields and malformed selector arrays fail closed.
4. Request timestamps require strict RFC3339 formatting and explicit timezone; a naive supplied clock is rejected.
5. Optional SQLite replay protection consumes a request ID inside an atomic write transaction. Concurrent duplicate attempts were tested.
6. Replay-store errors produce DENY rather than ALLOW.
7. The JSONL ledger rejects ambiguous JSON, non-integer sequence values, malformed record shapes, and non-standard numbers. Appends flush and fsync the file.
8. The structural verifier now checks contract catalog shape, required fields, IDs, versions, evidence lists, duplicate IDs, and contract-schema required-field metadata.

## Not tested / not claimed

- No penetration test, external red-team engagement, fuzzing campaign, property-based test campaign, or high-volume performance/load benchmark.
- No live OS sandbox, container escape, network egress, process isolation, kernel boundary, hardware attestation, or complete-mediation test.
- No identity-provider integration, signed policy, credential revocation, distributed replay cache, or replay-database anti-rollback test.
- No multi-process or multi-host JSONL writer test; the JSONL ledger remains single-writer.
- No recovery drill, signing-key compromise exercise, real MCP/A2A/ACS interoperability test, or independent assessor review.
- No production safety or certification claim.

## Residual highest-risk gaps

1. Identity and authority are still represented by caller-supplied strings, not authenticated credentials.
2. SQLite replay protection is optional, local, and vulnerable to database rollback/replacement by an attacker with write access. Fresh fabricated request IDs are not prevented.
3. A local policy file is not signed or protected against rollback.
4. No separate privileged execution broker currently enforces all protected side effects.
5. Delegation cycle rejection is not capability attenuation.
6. The JSONL ledger remains replaceable without an independent signed checkpoint and is not multi-writer safe.
7. The repository verifier is not a deployment conformance engine.

## Acceptance decision

The hardened reference layer is suitable for continued experimental development and local integration testing. It is not a standalone production security control. Deployments must place identity, policy integrity, replay storage, and enforcement behind independently protected boundaries appropriate to their threat model.
