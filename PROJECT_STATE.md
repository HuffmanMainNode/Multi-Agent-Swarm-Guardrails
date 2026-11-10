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
Status at checkpoint: CI passed; PR awaits final merge.

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

## Security limitations
Linux only. Processes sharing a UID share an identity. This is local OS identity, not cryptographic workload identity. Policy and UID map require operator-controlled files/directories and are loaded at startup. Local replay DB can be rolled back. Only audit append is exposed. No arbitrary tool executor, shell, filesystem proxy, network proxy, credential revocation, signed policy, anti-rollback, general sandbox, complete mediation proof, fuzz campaign, penetration test, or independent review.

## Next
After PR #4 merge, prioritize cryptographic workload identity/revocation and signed policy provenance/anti-rollback. Do not expand broker capabilities until each new operation has a fixed schema, explicit authority mapping, bounded inputs/resources, side-effect evidence, and bypass tests.
