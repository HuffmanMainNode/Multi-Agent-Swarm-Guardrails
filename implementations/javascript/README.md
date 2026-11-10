# MASG JavaScript Reference Evaluator

Dependency-free JavaScript implementation of the MASG v1.0.0 policy-decision subset. Requires Node.js 22 or later.

## Use

```js
import { evaluate, evaluateJSON } from "@masg/reference-javascript";

const result = evaluate(policy, request, new Date());
const rawResult = evaluateJSON(policyBytes, requestBytes, new Date());
```

The package includes TypeScript declarations. It does not require Python, Go, Rust, a MASG-hosted service, or third-party npm packages.

## Implemented

- Full v1.0.0 request envelope and exact policy-version binding.
- Deny-by-default exact principal/action/target/scope matching.
- Explicit DENY precedence, REVIEW_REQUIRED, ALLOW, and NO_MATCH.
- UUIDv4 and RFC3339 validity checks, six fractional digits, known offsets.
- Schema-aligned field/selector/rule limits and Unicode code-point counting.
- Strict bounded JSON parser rejects duplicate keys, invalid UTF-8, unpaired surrogates, non-standard constants, unknown fields, excessive nesting, trailing data and oversized input.
- Shared eight-vector decision/time suite and ten shared raw-parser negative fixtures.

## Not implemented

- Principal authentication, SPIFFE/SPIRE, X.509-SVID/mTLS, identity issuance, or revocation.
- Signed policies/envelopes, TUF, key management, or anti-rollback storage.
- Replay database, distributed replay protection, broker, protected executor, OS side-effect mediation, sandbox, or complete mediation.
- Evidence ledger, recovery, hardware attestation, or deployment conformance.
- Fuzzing, load testing, penetration testing, or independent security assessment.

The caller supplies the principal and JavaScript Date clock. Neither is authenticated by this package. An ALLOW is a policy decision, not proof that an action was safely executed.

Passing shared fixtures does not certify a deployment or establish MSC conformance. The implementation manifest and conformance report state its narrow scope.

## Offline localization helper

The `./localization` subpath exports `resolveMessage(sourcePack, localePack, messageId, options)`. It uses HUMAN_REVIEWED text by default, falls back to the source locale for untranslated or needs-revision entries, and requires explicit `{ allowMachineDrafts: true }` to use a MACHINE_DRAFT. It performs no network access or machine translation.

```js
import { resolveMessage } from "@masg/reference-javascript/localization";

const result = resolveMessage(englishPack, spanishPack, "masg.ui.authorization_denied");
console.log(result.text, result.locale, result.usedFallback);
```

The helper performs runtime consistency checks, not full JSON Schema or IANA BCP 47 registry validation. Validate packs against the repository schema before distribution.
