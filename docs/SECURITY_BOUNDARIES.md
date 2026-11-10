# Security Boundaries

## Implemented
The reference package parses local JSON; requires deny-by-default; matches principal/action/target/scope exactly; checks request validity times; rejects rudimentary delegation cycles; returns ALLOW, REVIEW_REQUIRED, or DENY; writes a local JSONL SHA-256 chain; verifies sequence and links; and checks repository structure.

## Not implemented
No principal authentication, revocation service, signed policy, signed evidence, trusted timestamp, immutable remote log, distributed replay cache, process isolation, OS sandbox, network mediation, complete action-path discovery, independent guardian, human approval binding, or legality decision. It does not prove all side effects traverse an adapter.

## Adopter requirements
Bind decisions to authenticated identities; protect policy source; mediate every protected side effect; use scoped credentials; implement revocation and replay protection; isolate enforcement where needed; protect evidence outside agent authority; and test deployed paths.

## Fail-closed
Unknown required security input must not receive ALLOW. Safe operational state depends on resource. Abruptly stopping an industrial controller can itself be dangerous; domain engineers must define safe states.
