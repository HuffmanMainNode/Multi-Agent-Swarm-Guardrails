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

## New critical engineering branch
Branch: security/independent-linux-execution-broker

Adds an experimental Linux-only separate-process broker for exactly one fixed operation: audit.append. It derives caller UID using SO_PEERCRED, maps UID to an operator-configured principal, does not accept client-supplied identity or operation fields, applies deny-by-default policy, limits request TTL to five minutes, consumes a request ID in SQLite, and appends bounded event data to a broker-owned ledger.

New CLI:
- masg broker serve --socket ... --policy ... --principal-map ... --replay-db ... --ledger ...
- masg broker append --socket ... --request ...

New tests exercise UID mapping, caller identity spoofing, schema restrictions, oversized event rejection, duplicate JSON, excessive TTL, policy denial, replay store failure, corrupt ledger, concurrent duplicate requests, and real Unix socket peer-credential roundtrip.

## Security limitations
Linux only. Processes sharing a UID share an identity. Policy and UID map require operator-controlled permissions and are loaded at startup. Local replay DB can be rolled back. Only audit append is exposed. No arbitrary tool executor, shell, filesystem proxy, network proxy, cryptographic workload identity, revocation, signed policy, anti-rollback, general sandbox, complete mediation proof, fuzz campaign, penetration test, or independent review.

## Next
Wait for the new CI matrix. Investigate all failures from logs before changes. Merge only after the complete matrix and tests pass. Then perform a final source/tree review and update the register with exact CI and merge evidence.
