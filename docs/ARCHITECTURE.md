# Architecture

MASG is a portable contract, verification, and enforcement-integration layer, not an agent framework or hosted control plane.

## Layers
1. Agent application: model, prompts, orchestration, memory, planning.
2. Protocol interfaces: tool calls, MCP, A2A, framework APIs. Treat input/output as untrusted.
3. Identity and policy: adopter-selected identity provider and policy engine.
4. MASG adapter: bind identity, provenance, action, target, scope, expiry, delegation, policy, and risk disposition.
5. Protected executor: tool/API/filesystem/remote service holding narrowly scoped credentials.
6. Evidence: export decisions and results to a trust domain the agent cannot rewrite.

## Protected action flow
Agent proposes typed request -> adapter binds authenticated caller -> validate provenance -> evaluate policy/authority -> risk/approval disposition -> independent enforcement -> constrained execution -> evidence -> reconcile requested and executed actions.

Model output is a request, never authorization. A signature does not establish trust or safety. In-process Python cannot contain hostile code controlling the same interpreter.

## Experimental Linux broker

The first separate-process broker deliberately exposes one fixed operation, `audit.append`. It derives caller UID from Linux Unix-socket peer credentials, maps that UID to an operator-configured principal, authorizes the fixed operation, consumes a request ID in SQLite, and appends a bounded event to its own ledger. It accepts no caller-supplied principal, operation, target, scope, path, executable, or command.

The broker is an example of a protected side-effect boundary, not a general tool executor. It depends on OS UID separation, socket directory ownership, broker service account isolation, protected configuration, and broker-owned state. It is Linux-only.

## Failure handling
Unknown authorization state is not permission. Define safe state per protected resource. Safe-stop may be scoped to tool, session, delegation chain, agent, node, or swarm segment. No universal remote shutdown mechanism is provided.

## Current implementation
Local evaluator, JSONL ledger, structural verifier, and experimental Linux audit-append broker. No external identity provider, signed policy, general OS isolation, network mediation, complete path coverage, remote revocation, or hardware attestation.
