# Engineering Register

Last updated: 2026-11-10

| Area | Status | Evidence and limitation |
|---|---|---|
| Ten mandatory contracts | Specified | Machine-readable catalog; only a subset of requirements is executable |
| Universal protocol v1.0.0 | Implemented specification baseline | Normative language-neutral decision semantics, versioning, trust boundaries, policy-version binding, JSON Schemas and portable vectors; merged PR #10 |
| Portable conformance artifacts | PASS in PR CI | JSON Schema Draft 2020-12 validation and shared decision vectors run against Python 3.11/3.12/3.13; PR run 42746824887 passed; this is not deployment certification |
| Independent language implementations | Python and Go reference implementations | Go uses only the standard library and passes five shared v1.0.0 policy-decision vectors; it is embedded-only and does not authenticate principals or mediate side effects; no Rust/Java/C#/TypeScript implementation yet |
| Namespaced extension model | Specified | Versioned extension manifest schema, domain/transport/identity/policy/enforcement/evidence/recovery types, fail-closed compatibility rules; example is documentation-only; merged PR #13 |
| Go portable decision conformance | PASS in CI, narrowly scoped | Go vet and race-enabled tests pass; five shared vectors; PR run 42748191713 and main run 42748296088; report scope is policy-decision vectors only, not MSC certification |
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

Independent Rust/Java/C#/TypeScript implementations and broader cross-language interoperability testing; full conformance runner for deployment profiles; signed protocol envelope/canonicalization profile; sender-constrained identity (X.509-SVID/mTLS); live SPIRE rotation/revocation and workload-selector tests; review and hash-pin the optional py-spiffe dependency closure (pinned release currently has no PyPI provenance); stronger rollback-resistant TUF cache storage; TUF repository publishing/signing workflow and key management; distributed anti-replay; capability-set delegation attenuation; typed protected executor beyond audit append; complete mediation and bypass testing; stronger OS isolation; independently checkpointed evidence; deployment-level conformance; fuzzing/load/penetration testing; independent security review.

## Validation boundary

The Go implementation passed Go vet and race-enabled tests against the shared five-vector v1.0.0 policy-decision suite. Its report is explicitly scoped to those vectors; its MSC contract statuses remain NOT_TESTED. It does not authenticate principals or enforce side effects. The extension manifest schema and documentation example passed CI, but no extension adapter is implemented or trusted by virtue of its manifest.



PR #8's SPIFFE integration passed its 75-test Python 3.11/3.12/3.13 matrix, Ruff, structural verification, and JSON checks. The tests use an injected fake Workload API client; they do not exercise a live SPIRE Agent or prove revocation propagation. The optional dependency is third-party and has a documented provenance gap. JWT-SVID is a bearer credential, not sender-constrained. No production deployment, complete mediation, safety certification, or independent review is established.


## Cross-language parity checkpoint

The v1.0.0 shared-vector harness now passes the complete request envelope to Python's `evaluate_protocol`, rather than stripping protocol fields before evaluation. Python and Go now align with the published schema for rule IDs, 1,000-rule and 128-selector limits, field-specific selector lengths, Unicode code-point counting, policy/request JSON byte caps, optional provenance references, and RFC 3339 timestamp precision/known-offset behavior. CI evidence is pending for PR `protocol/cross-language-semantic-parity`; do not describe these changes as merged or passed until the run completes.
