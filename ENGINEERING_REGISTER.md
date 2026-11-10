# Engineering Register

Last updated: 2026-11-10

| Area | Status | Evidence and limitation |
|---|---|---|
| Ten mandatory contracts | Specified | Machine-readable catalog; only a subset of requirements is executable |
| Universal protocol v1.0.0 | Implemented specification baseline | Normative language-neutral decision semantics, versioning, trust boundaries, policy-version binding, JSON Schemas and portable vectors; merged PR #10 |
| Shared parser-negative fixtures | PASS in CI | Ten hex-encoded malformed raw-document fixtures run unchanged through Python, Go and Rust; PR #20 run 42761090847 and post-merge main run 42761152825 passed; deterministic regression baseline, not exhaustive fuzzing |
| Portable conformance artifacts | PASS in PR CI | JSON Schema Draft 2020-12 validation and shared decision vectors run against Python 3.11/3.12/3.13; PR run 42746824887 passed; this is not deployment certification |
| Independent language implementations | Python, Go, and Rust reference implementations | Go 0.1.1 and Rust 0.1.0 are independent standard-library-only evaluators; both pass the same eight shared v1.0.0 decision/time vectors plus strict parser/limit tests; embedded-only, no principal authentication or side-effect mediation; no Java/C#/TypeScript implementation yet |
| Namespaced extension model | Specified | Versioned extension manifest schema, domain/transport/identity/policy/enforcement/evidence/recovery types, fail-closed compatibility rules; example is documentation-only; merged PR #13 |
| Go portable decision conformance | PASS in CI, narrowly scoped | Go vet and race-enabled tests pass; eight shared vectors; PR #16 CI run 42750992748 and post-merge main run 42751069709; report scope is policy-decision/time vectors only, not MSC certification |
| Strict policy/request parsing | Implemented in reference evaluator | Duplicate keys, non-standard constants, unknown fields, malformed selectors, and oversized inputs rejected |
| Policy evaluator | Experimental reference implementation | Deny-by-default, exact selectors, explicit deny precedence, expiry checks |
| Identity/revocation | Experimental optional SPIFFE JWT-SVID mode | Per-request Workload API validation for exact audience; validated SPIFFE ID becomes policy principal; request expiry bounded by SVID expiry; legacy UID mode remains; bearer-token limitations apply |
| Replay resistance | Local reference control | SQLite atomic one-time UUIDv4 request-ID consumption in broker; rollback/fresh IDs remain possible |
| Evidence ledger | Experimental local format | SHA-256 chain; broker serializes its own appends; no independent checkpoint or anti-rollback |
| Structural verifier | Implemented | Checks repository structure/catalog shape; does not verify deployments |
| Policy publisher authentication | Optional experimental TUF client | python-tuf 7.0.1 verifies metadata signatures, versions, expiry, snapshot consistency, and policy target hashes from a local mirror; bootstrap root is out-of-band; cache rollback protection is an adopter responsibility; merged PR #6 |
| Independent execution broker | Implemented as experimental Linux reference | Separate process, SO_PEERCRED transport provenance, UID mapping or optional SPIFFE JWT-SVID principal, fixed audit.append allowlist, five-minute TTL, UUIDv4 IDs, bounded inputs, 32-handler cap |
| Broker configuration | Hardened baseline | Rejects symlink/special config files and group/world-writable config/state/socket parent directories; SPIFFE endpoint path components also checked |
| Broker and TUF tests | PASS in CI | 57 tests per Python version, 3.11/3.12/3.13; TUF PR #6 and main runs passed |
| SPIFFE adapter tests | PASS in CI | 75 tests per Python 3.11/3.12/3.13 job; PR #8 tested head bb482dcefc1184350b76122ea9bc33c56e35d98c; merged as afac8e19a9d979158ec048c4261a5a993dce39e5; PR run 42744847753 and main run 42744955882 passed |
| General tool mediation | Not implemented | No arbitrary tool, filesystem, network, shell, or executable execution |
| Independent review | Not performed | No certification or external audit claim |

## Critical gaps

Java/C#/TypeScript implementations and broader cross-language differential/property/fuzz testing; full conformance runner for deployment profiles; signed protocol envelope/canonicalization profile; sender-constrained identity (X.509-SVID/mTLS); live SPIRE rotation/revocation and workload-selector tests; review and hash-pin the optional py-spiffe dependency closure (pinned release currently has no PyPI provenance); stronger rollback-resistant TUF cache storage; TUF repository publishing/signing workflow and key management; distributed anti-replay; capability-set delegation attenuation; typed protected executor beyond audit append; complete mediation and bypass testing; stronger OS isolation; independently checkpointed evidence; deployment-level conformance; fuzzing/load/penetration testing; independent security review.

## Validation boundary

The Go implementation 0.1.1 passed Go vet and race-enabled tests against the shared eight-vector v1.0.0 policy-decision/time suite. Its report is explicitly scoped to those vectors; its MSC contract statuses remain NOT_TESTED. It does not authenticate principals or enforce side effects. The extension manifest schema and documentation example passed CI, but no extension adapter is implemented or trusted by virtue of its manifest.



PR #8's SPIFFE integration passed its 75-test Python 3.11/3.12/3.13 matrix, Ruff, structural verification, and JSON checks. The tests use an injected fake Workload API client; they do not exercise a live SPIRE Agent or prove revocation propagation. The optional dependency is third-party and has a documented provenance gap. JWT-SVID is a bearer credential, not sender-constrained. No production deployment, complete mediation, safety certification, or independent review is established.


## Cross-language parity checkpoint

The v1.0.0 shared-vector harness now passes the complete request envelope to Python's `evaluate_protocol`, rather than stripping protocol fields before evaluation. Python and Go now align with the published schema for rule IDs, 1,000-rule and 128-selector limits, field-specific selector lengths, Unicode code-point counting, policy/request JSON byte caps, optional provenance references, and RFC 3339 timestamp precision/known-offset behavior. PR #16 merged as `019cd466583779fe38441ef5e62be32e5b1cc191`; CI run 42750992748 passed and post-merge main CI 42751069709 passed.


Cross-language raw parser parity: Python `evaluate_protocol_json` and Go `EvaluateJSON` reject duplicate keys, invalid UTF-8, non-standard JSON constants, non-object envelopes, unknown fields, excessive nesting and over-limit byte sizes. This is parser/evaluator conformance only; it is not identity or enforcement certification.


## Cross-language parity evidence

PR #16 tested head `1b95c53aefd366f5364417b5bdfc6f07b78b95a8`; CI run 42750849476 passed Python 3.11/3.12/3.13 and Go vet/race tests. The Python shared-vector harness now evaluates the complete request envelope; Python `evaluate_protocol_json` and Go `EvaluateJSON` apply equivalent strict raw-JSON checks. Both implementations match the schema's rule IDs, array and field limits, Unicode code-point semantics, optional provenance field, timestamp precision and JSON depth/size boundaries. Eight vectors are covered; MSC statuses remain untested and no deployment assurance is claimed.


## Current main checkpoint

Main commit `019cd466583779fe38441ef5e62be32e5b1cc191`; post-merge CI `42751069709` passed Python 3.11/3.12/3.13 and Go. Python and Go share eight vectors and aligned strict input limits. Go conformance is still limited to embedded policy decision/time vectors; all ten MSC statuses remain NOT_TESTED.


## Rust implementation checkpoint

A third implementation is under review in `implementations/rust/`. It uses only the Rust standard library and has its own strict JSON parser. Status remains NOT_TESTED until the Rust CI job compiles and executes the shared vectors. Do not count it as a supported implementation or conformance PASS before CI succeeds.


## Rust reference status

Rust 0.1.0 under `implementations/rust/` passed CI run 42752336251: rustfmt, Clippy with warnings denied, and shared-vector/parser tests. The implementation is dependency-free and passes all eight v1.0.0 decision/time vectors. Its report scope is only those vectors; all MSC statuses remain NOT_TESTED. It does not authenticate principals or mediate side effects. PR #18 is open pending final merge.


## Three-language conformance evidence

- Python reference evaluator: shared eight-vector suite plus Python parser/schema regression tests in the main Python 3.11/3.12/3.13 matrix.
- Go 0.1.1: eight shared policy/time vectors; Go vet and race-enabled tests; tested source revision `1b95c53aefd366f5364417b5bdfc6f07b78b95a8`; CI run 42750849476 passed.
- Rust 0.1.0: eight shared policy/time vectors; strict parser, UTF-8, duplicate-key, unknown-field, timestamp and boundary tests; tested source revision `0cc0a0ac4baa906f3757c970f8d881f1ec365ca5`; CI run 42752336251 passed.
- Post-merge main CI run 42752581046 passed Python 3.11/3.12/3.13, Go vet/race, Rust formatting, Clippy with warnings denied, and Rust tests.
- The eight vectors are not a full conformance suite. All ten MSC statuses remain NOT_TESTED in both Go and Rust manifests. No deployment certification or independent security assessment is implied.


## Parser-negative regression evidence

PR #20 merged as `31f3c9d1f60bf71363250965a2db32d811cd9d3d`. Tested head `283bc384f3c5a9f00e67289ed543282a2906b51b`; PR CI run 42761090847 passed; post-merge main CI run 42761152825 passed. Ten shared raw-byte fixtures are executed by Python, Go, and Rust. These cases prove only the listed failure behaviors. They are not a fuzz campaign, memory-safety assessment, or full protocol conformance result.
