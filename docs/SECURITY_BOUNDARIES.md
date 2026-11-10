# Security Boundaries

## Implemented
The reference package parses local JSON; requires deny-by-default; matches principal/action/target/scope exactly; checks request validity times; rejects rudimentary delegation cycles; returns ALLOW, REVIEW_REQUIRED, or DENY; writes a local JSONL SHA-256 chain; verifies sequence and links; checks repository structure; and includes an experimental separate-process Linux broker for one fixed audit append operation.

The broker derives peer UID through Linux SO_PEERCRED, maps it to a configured principal, rejects caller-supplied identity/operation fields, applies a five-minute maximum request lifetime, consumes request IDs locally, and appends bounded events to its own ledger.

## Not implemented
No cryptographic workload identity, credential issuance/revocation, signed evidence, trusted timestamp, immutable remote log, distributed replay cache, arbitrary-tool broker, general filesystem/network mediation, complete action-path discovery, independent guardian, human approval binding, or legality decision. Optional TUF-backed policy publisher authentication is available through a local mirror; static policy mode remains unsigned and TUF cache rollback protection depends on protected persistent storage. It does not prove all application side effects traverse the broker.

## Adopter requirements
Use distinct OS identities for agents; bind decisions to authenticated identities; protect policy source; mediate every protected side effect; use scoped credentials; implement revocation and replay protection; isolate enforcement where needed; protect evidence outside agent authority; and test deployed paths.

## Fail-closed
Unknown required security input must not receive ALLOW. Safe operational state depends on resource. Abruptly stopping an industrial controller can itself be dangerous; domain engineers must define safe states.
