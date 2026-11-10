# MASG Rust Reference Evaluator

Independent, dependency-free Rust implementation of the MASG v1.0.0 policy-decision subset.

## Build and test

Requires stable Rust and Cargo. Run cargo fmt --check, cargo test --locked, and cargo clippy --all-targets -- -D warnings.

The crate uses only the Rust standard library. It implements a bounded strict JSON parser with duplicate-key detection, UTF-8 validation, JSON depth limits, strict string escape handling, and no third-party parser dependency.

## Implemented

- Complete v1.0.0 policy and authorization-request envelope parsing.
- Deny-by-default exact principal/action/target/scope matching.
- Explicit DENY precedence, REVIEW_REQUIRED, ALLOW, and NO_MATCH.
- Exact policy-version binding, canonical lowercase UUIDv4 validation, expiry checks.
- RFC 3339 timestamps with zero to six fractional digits and known explicit offsets.
- Schema-aligned policy/rule/selector limits and Unicode code-point counting.
- Strict JSON duplicate-key, unknown-field, invalid UTF-8, nesting-depth and byte-size rejection.
- Optional non-authoritative provenance_ref.
- Shared eight-vector test suite plus parser/limit regression tests.

## Not implemented

- Principal authentication, SPIFFE/SPIRE, X.509-SVID/mTLS, credential issuance, or revocation.
- Signed policy or signed envelopes, TUF, key management, or anti-rollback storage.
- Replay database, distributed replay protection, broker, protected executor, filesystem/network mediation, sandbox, or complete mediation.
- Evidence ledger, recovery, hardware attestation, or deployment conformance.
- Fuzzing, load testing, penetration testing, or independent security assessment.

The caller supplies now_unix_micros; the crate does not provide trusted time. The principal is an input assertion and must be derived by an external trusted identity adapter. This implementation is an embedded policy evaluator only.

A vector PASS means agreement with the listed protocol outcomes under the test clock. It is not security certification or production readiness.
