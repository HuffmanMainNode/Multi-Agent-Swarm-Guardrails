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

New CLI:
- masg broker serve --socket ... --policy ... --principal-map ... --replay-db ... --ledger ...
- masg broker append --socket ... --request ...

## Validation evidence
Two successful CI runs on the tested head:
- 42735881467
- 42735881291

All Python 3.11, 3.12, and 3.13 jobs passed. Each ran 46 unit tests, package installation, structural verification, and JSON syntax checks. The first broker CI run failed two new validation tests; parser depth and UUID validation were corrected before the successful runs. Details are in docs/STRESS_TEST_RESULTS.md.

## Optional TUF policy source
The broker can load a policy target from a local TUF mirror using python-tuf. The bootstrap root is supplied out-of-band, and the metadata cache persists under an operator-controlled directory. TUF signature, version, expiry, snapshot, and target hash checks must pass before the policy is loaded. Static policy mode remains available but is not publisher-authenticated. MASG does not publish TUF repositories or manage private signing keys. The cache can still be rolled back by an attacker who can restore older cache state.

## TUF validation evidence
PR #6 merged as `e8a8d1400a601ef4277ed388337f630c06531cf2`; branch `security/tuf-policy-trust-and-rollback`, tested head `ba950ae7a69ffe77202d786623fdefb662ae1cd1`. CI runs 42737352852 and 42737349896 passed all Python 3.11, 3.12, and 3.13 jobs; main-branch CI run 42737605525 also passed. Each ran 57 tests plus Ruff, structural verification, and JSON checks. Tests include signed target acceptance, target and metadata tampering, timestamp rollback, expired metadata, wrong bootstrap root, path traversal, unsafe cache permissions, broker startup from verified policy, and fail-closed tamper behavior.

## Security limitations
Linux only. Processes sharing a UID share an identity. This is local OS identity, not cryptographic workload identity. Policy and UID map require operator-controlled files/directories and are loaded at startup. Optional TUF mode authenticates policy publisher metadata, but its cache can be rolled back if an attacker controls persistent cache storage. Local replay DB can be rolled back. Only audit append is exposed. No arbitrary tool executor, shell, filesystem proxy, network proxy, credential revocation, TUF repository publishing/key management, rollback-resistant cache storage, general sandbox, complete mediation proof, fuzz campaign, penetration test, or independent review.

## Next
Prioritize cryptographic workload identity/revocation, a TUF repository publishing/signing workflow, and stronger rollback-resistant cache storage. Do not expand broker capabilities until each new operation has a fixed schema, explicit authority mapping, bounded inputs/resources, side-effect evidence, and bypass tests.
