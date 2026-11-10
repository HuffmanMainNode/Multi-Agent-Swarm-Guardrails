# Engineering Register

Last updated: 2026-11-09

| Area | Status | Evidence and limitation |
|---|---|---|
| Ten contract catalog | Specified | Machine-readable manifest; not all enforced |
| Policy evaluator | Reference implementation | Exact local matching, expiry, deny-by-default; explicit deny now takes precedence |
| Identity/revocation | Not implemented | Principal strings are not authenticated |
| Delegation attenuation | Not implemented | Rudimentary cycle rejection only |
| Evidence ledger | Reference implementation | Local SHA-256 chain; not signed, immutable, or multi-writer safe |
| Structural verifier | Implemented | Repository structure only |
| JSON schemas | Draft | Not yet enforced by CLI |
| Deployment profiles | Specification | No runtime profile verification |
| Tests | Added | CI run 42732531500 passed on Python 3.11, 3.12, and 3.13 for commit a46593edfe093b01cf7b8d87f6fd09ad23b5d11e |
| Latest hardening commit | Pending validation | afc7d8279403ac791ad9ca79cad79b582028cff3 adds deny precedence and stricter ledger record shape; must be retested |
| Independent review | Not performed | No certification or audit claim |

## Critical gaps
External authentication/revocation; signed policy provenance; persistent replay protection; delegation attenuation; independent execution broker; complete mediation; OS isolation; protected evidence checkpoint; contract-level conformance; fuzzing; independent review.

The successful CI run above applies to its recorded commit only. Do not transfer that PASS status to later commits until CI reruns. No independent security review or deployment certification has occurred.
