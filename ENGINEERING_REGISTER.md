# Engineering Register

Last updated: 2026-11-09

| Area | Status | Evidence and limitation |
|---|---|---|
| Ten contract catalog | Specified | Machine-readable manifest; not all enforced |
| Policy evaluator | Reference implementation | Exact local matching, expiry, deny-by-default |
| Identity/revocation | Not implemented | Principal strings are not authenticated |
| Delegation attenuation | Not implemented | Rudimentary cycle rejection only |
| Evidence ledger | Reference implementation | Local SHA-256 chain; not signed or immutable |
| Structural verifier | Implemented | Repository structure only |
| JSON schemas | Draft | Not yet enforced by CLI |
| Deployment profiles | Specification | No runtime profile verification |
| Tests | Added, execution pending | Record actual command results after running |
| CI | Added, first run pending | Inspect Actions before claiming pass |
| Independent review | Not performed | No certification or audit claim |

## Critical gaps
External authentication/revocation; signed policy provenance; persistent replay protection; delegation attenuation; independent execution broker; complete mediation; OS isolation; protected evidence checkpoint; contract-level conformance; fuzzing; independent review.

No test is marked PASS until actual execution is observed. Update this register with exact commit and CI run IDs when known.
