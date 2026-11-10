# Integration Guide

Place MASG at the protected side-effect boundary. Do not rely on prompts, agent self-report, or UI confirmation as sole authorization.

1. Receive a typed action request.
2. Bind it to authenticated principal from host identity system.
3. Normalize action and target; reject ambiguous identifiers.
4. Load protected, versioned policy.
5. Evaluate exact principal, action, target, scope, validity, and delegation.
6. Obtain independently bound approval for REVIEW_REQUIRED.
7. Execute through broker holding credentials.
8. Record request, decision, executed action, result, and policy version.
9. Reconcile request, execution, and observed result.

## MCP
Treat server identity, tool definitions, schemas, annotations, arguments, and results as security input. Pin and review server versions. Enforce at server/broker, not only client. No MCP adapter is included.

## A2A
Bind messages to sender, recipient, audience, type, payload, creation/expiry, unique message ID, and delegation. Authenticate and authorize independently; reject replay. No A2A adapter is included.

## Offline
Core package and verifier require no network. Optional adapters may use external services, but no MASG-hosted endpoint is required.
