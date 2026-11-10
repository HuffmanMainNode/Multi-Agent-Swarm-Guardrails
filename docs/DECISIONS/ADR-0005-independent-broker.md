# ADR-0005: Narrow Independent Linux Execution Broker

- Status: Accepted for experimental reference implementation
- Date: 2026-11-10
- Owner: MrCakes931

## Context

The local evaluator returns decisions but cannot prevent an application from bypassing it or executing a side effect directly. A generic command runner would create an unnecessarily dangerous attack surface and would not prove safe mediation.

## Decision

Implement a separate-process Linux Unix-domain-socket broker with OS peer credentials. Map the connecting UID to an operator-configured principal. Accept no caller-supplied principal or operation fields. Authorize exactly one operation, `audit.append`, against a fixed target and scope. Consume a request ID in SQLite before appending a bounded event to the broker-owned ledger. Return ALLOW only after the append call succeeds.

Bound message size, event detail length, request lifetime, read time, and concurrent handlers. Refuse symlink/special config files, writable config files, existing socket paths, and aliased replay/ledger paths.

## Why only one operation

A narrow allowlisted side effect is auditable and testable. Arbitrary shell, executable, filesystem, network, or tool invocation would substantially expand the threat surface before a capability registry and isolation model exist.

## Assumptions and limitations

- Linux `SO_PEERCRED` is the identity source. All processes sharing an OS UID share this broker identity.
- Broker service account, OS kernel, policy files, principal map, socket parent, replay DB, and ledger are trusted within the deployment threat model.
- Policy is loaded at startup and is not signed or anti-rollback protected.
- Replay state is local and can be rolled back by an attacker controlling broker state.
- The broker does not prove all application side effects are mediated.
- A compromised broker or host administrator can alter outcomes.
- No Windows/macOS implementation is claimed.

## Consequences

The repository now has an executable example of independent mediation for one fixed protected operation. Future adapters must be added as explicit typed capabilities with separate threat analysis and tests. Do not turn this broker into a general shell or arbitrary-command service.
