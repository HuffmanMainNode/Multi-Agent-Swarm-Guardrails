# Implementing MASG in Any Language

This guide is for independent implementers. You do not need Python or the MASG package.

## Required inputs

- `spec/README.md` and the normative specification.
- JSON Schemas under `schemas/`.
- Contract catalog at `contracts/manifest.json`.
- Versioned test vectors under `vectors/`.

## Minimum implementation sequence

1. Parse UTF-8 JSON with duplicate-key detection, reject NaN/Infinity, bound bytes and nesting, and reject unknown normative fields.
2. Validate policy/request/response structures against JSON Schema Draft 2020-12.
3. Implement exact principal/action/target/scope matching and deny-by-default.
4. Apply precedence: DENY, then REVIEW_REQUIRED, then ALLOW, then default DENY.
5. Validate request ID, timezone-aware timestamps, expiry and trusted clock assumptions.
6. Derive principal from an authenticated identity adapter. Never trust an untrusted request's principal string.
7. Fail closed if identity, policy integrity, replay storage, or other required controls are unavailable.
8. Run every applicable portable conformance vector.
9. Add runtime-specific tests for actual side-effect paths and bypasses.
10. Publish a truthful implementation manifest and conformance report.

## Language and runtime support

Any language may implement the protocol if it preserves the normative semantics. A language binding may provide idiomatic APIs, but MUST NOT alter wire behavior or weaken security requirements. It may use native JSON, crypto, IPC, database, identity and sandbox libraries.

## Test-vector expectations

Each vector includes a policy, request and expected decision/reason code. Implementations should run vectors without modifying their contents. If a vector cannot be run because a control is not implemented, report NOT_TESTED or NOT_APPLICABLE with a reason; do not omit it from the report.

## What a conformance pass means

A pass means the implementation matched the specified result for the tests actually run in the declared environment. It does not prove production readiness, security against unknown attacks, safe behavior of every integrated tool, complete mediation, or legal compliance.

## Extensions and domain adaptation

When a domain or transport needs adaptation, prefer a namespaced extension over changing the core protocol. See [the extension model](EXTENSION_MODEL.md). Keep core invariants intact, publish extension schemas and vectors, and fail closed when a required security-critical extension is unavailable. A compatible extension does not need a central registry or approval.

## Contributions

A new language implementation should live in its own directory, e.g. `implementations/rust/` or `implementations/go/`, and include:
- source and build instructions;
- dependency and license inventory;
- language/runtime support statement;
- automated schema/vector tests;
- threat model and limitations;
- implementation manifest and conformance report;
- CI that can be reproduced locally.

Keep the normative schemas and vectors implementation-neutral. Do not add language-specific assumptions to the protocol core.
