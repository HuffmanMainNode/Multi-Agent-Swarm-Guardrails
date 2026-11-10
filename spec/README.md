# MASG Universal Protocol Specification

This directory contains the normative, language-neutral protocol specification. It is deliberately separate from the Python reference package under `src/masg/`.

## Version 1.0.0 scope

The first protocol version standardizes:
- exact-match deny-by-default policy document shape;
- authorization decision request and response envelopes;
- portable implementation manifests;
- conformance reports and portable test-vector format;
- versioning, error behavior, trust boundaries, and namespaced extension-package rules.

It does not standardize an execution broker transport, identity provider, cryptographic signature format, sandbox, model interface, or agent orchestration protocol. Those remain adapter/profile concerns.

## Normative artifacts

- `../schemas/decision-policy.schema.json`
- `../schemas/decision-request.schema.json`
- `../schemas/decision-response.schema.json`
- `../schemas/implementation-manifest.schema.json`
- `../schemas/conformance-report.schema.json`
- `../schemas/conformance-vector.schema.json`
- `../schemas/extension-manifest.schema.json`
- `../vectors/v1.0.0/`
- `../docs/EXTENSION_MODEL.md`

JSON Schema Draft 2020-12 is normative for structural validation. Implementations MUST reject duplicate JSON object keys, non-finite numeric constants, unknown fields in protocol envelopes, invalid UTF-8, and values exceeding declared limits. A schema-valid document is not necessarily authorized or safe.

## Protocol invariants

1. A model output, prompt, message, tool description, or peer assertion is never authorization.
2. A principal in a decision request MUST be derived by a trusted adapter from authenticated identity. Untrusted callers MUST NOT choose it.
3. Identity, authentication, trust, authorization, and safe execution are separate claims.
4. Missing, malformed, expired, unavailable, or contradictory authority MUST NOT produce ALLOW.
5. Explicit DENY dominates any matching ALLOW.
6. Policy default is DENY. Wildcard matching is not defined in v1.0.0.
7. Request validity MUST be checked against a trusted, timezone-aware clock. The protocol does not itself provide trusted time.
8. An ALLOW is a decision only. It does not prove that a protected operation was executed through an enforcement boundary.
9. Implementations MUST preserve unknown security limitations and MUST NOT claim support for contracts or profiles they have not tested.
10. Standard v1.0.0 reason codes include `EXPLICIT_MATCH`, `EXPLICIT_DENY`, `APPROVAL_REQUIRED`, `NO_MATCH`, `POLICY_VERSION_MISMATCH`, `EXPIRED`, `NOT_YET_VALID`, and `INVALID_VALIDITY_WINDOW`. Other invalidity/failure reason codes are implementation-specific unless a later version standardizes them.
11. Test and conformance outcomes are PASS, FAIL, UNKNOWN, NOT_TESTED, or NOT_APPLICABLE. Missing evidence is not PASS.

## Decision algorithm

For a structurally valid, authenticated request:
1. Validate protocol version, request identifier, timestamp syntax and validity window.
2. Resolve identity using the adapter's declared trust mechanism. Do not trust caller-supplied principal fields without independent verification.
3. Load a trusted policy version, require the request's policy_version to match it exactly, and verify its integrity according to the deployment profile.
4. Collect rules whose principal, action, target, and scope each exactly match.
5. If any matching rule has effect DENY, return DENY.
6. Otherwise, if any matching rule has effect REVIEW_REQUIRED, return REVIEW_REQUIRED.
7. Otherwise, if any matching rule has effect ALLOW, return ALLOW.
8. Otherwise return DENY with reason code NO_MATCH.
9. On any error or unavailable required control, do not return ALLOW.

This algorithm is a specification target. The Python evaluator/broker and independent Go evaluator implement different subsets; the Go report passes only the five portable policy-decision vectors in the embedded profile. Neither result certifies all contracts or a deployed system; consult each implementation manifest, contract status and limitations.

## Versioning and extensibility

- MAJOR: incompatible semantics, field removal/renaming, changed security meaning, or changed default behavior.
- MINOR: backward-compatible optional fields, new defined categories, or new test vectors.
- PATCH: editorial clarification or corrections that do not change protocol semantics.
- A receiver MUST reject unsupported major versions.
- A receiver MAY reject unsupported minor versions; it MUST NOT silently ignore unknown security-critical fields.
- V1.0.0 forbids arbitrary extension fields in normative envelopes. It defines an out-of-band, namespaced extension-package model in [docs/EXTENSION_MODEL.md](../docs/EXTENSION_MODEL.md). Extensions that require new security-critical envelope fields or decision semantics require a versioned core protocol change.
- Never reinterpret a prior field to mean a weaker security property.

## Transport and language neutrality

The protocol is independent of HTTP, Unix sockets, pipes, message queues, gRPC, MCP, A2A, or any programming language. A transport adapter maps transport messages to these envelopes and MUST preserve request identity, expiry, authenticated identity provenance, and failure semantics. Language implementations MUST consume the same JSON Schemas and conformance vectors.

## Canonicalization and signatures

V1.0.0 does not define signed protocol envelopes or a canonical JSON signature representation. Do not sign arbitrary serializer output and assume cross-language byte equivalence. A future signed profile must select a reviewed canonicalization standard, key discovery and rotation rules, anti-rollback metadata, revocation behavior, and test vectors before claiming signature interoperability.

## Limits

The initial schemas impose bounded field lengths and array sizes. Implementations MUST also enforce an overall message-size limit, parser-depth limit, connection/resource limits, and bounded timeouts appropriate to their deployment. Limits MUST be documented and no less restrictive than the deployment can safely support.

## Conformance claims

Conformance is per implementation, version, protocol version, profile, and tested environment. A passing schema test does not establish identity security, complete mediation, isolation, side-effect safety, resilience, or production readiness. Reports MUST state test scope, skipped tests, environment, source revision, and limitations.
