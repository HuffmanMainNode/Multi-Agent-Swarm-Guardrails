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

## Failure handling
Unknown authorization state is not permission. Define safe state per protected resource. Safe-stop may be scoped to tool, session, delegation chain, agent, node, or swarm segment. No universal remote shutdown mechanism is provided.

## Current implementation
Local evaluator, JSONL ledger, and structural verifier only. No external identity, signed policy, OS isolation, network mediation, complete path coverage, remote revocation, or hardware attestation.
