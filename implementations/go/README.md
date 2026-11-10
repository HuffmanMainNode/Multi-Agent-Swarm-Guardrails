# MASG Go Reference Evaluator

Independent Go implementation of the MASG v1.0.0 policy-decision subset.

## Build and test

Requires Go 1.23 or later. No third-party Go modules are required.

```sh
go test ./...
go test -race ./...
go vet ./...
```

The tests load the shared fixtures from `../../vectors/v1.0.0/decision-vectors.json`. The initial v1.0.0 portable policy-decision vector suite passed in CI run [42747836468](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails/actions/runs/42747836468) using `go test -race -count=1 ./...`. Do not edit expected outcomes to make an implementation pass; investigate semantic disagreement first.

## Implemented

- MASG v1.0.0 request envelope and exact policy-version binding.
- Exact principal/action/target/scope matching.
- Deny-by-default, explicit DENY precedence, REVIEW_REQUIRED, and ALLOW.
- Request UUIDv4 syntax and RFC3339 timestamp/expiry checks.
- Duplicate JSON key rejection, unknown-field rejection, bounded input size and nesting.
- Portable shared decision-vector execution.

## Not implemented

- Identity authentication, credential issuance, revocation, SPIFFE, mTLS or sender-constrained identity.
- Policy signature/TUF verification, secure policy distribution or anti-rollback storage.
- Replay database or distributed replay protection.
- Broker, protected executor, operating-system side-effect mediation, sandbox, network/filesystem controls, or complete mediation.
- Evidence ledger, signed evidence, recovery controls, hardware attestation or deployment conformance.
- Fuzzing, load testing, penetration testing or independent assessment.

The `principal` field is an input assertion to this evaluator. A real deployment MUST derive it from a trusted identity adapter before calling this package. This implementation currently supports only the embedded profile, where the host process is assumed trusted.

A passing vector suite means only that this implementation agrees with the listed decision semantics under the test clock. It is not a security certification or production-readiness claim.
