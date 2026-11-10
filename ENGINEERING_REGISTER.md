# Engineering Register

Last updated: 2026-11-10

| Area | Status | Evidence and limitation |
|---|---|---|
| Ten mandatory contracts | Specified | Machine-readable catalog; only a subset of requirements is executable |
| Strict policy/request parsing | Implemented in reference evaluator | Duplicate keys, non-standard constants, unknown fields, malformed selectors, and oversized inputs rejected |
| Policy evaluator | Experimental reference implementation | Deny-by-default, exact selectors, explicit deny precedence, expiry checks |
| Identity/revocation | Not implemented | Principal strings are caller assertions, not authenticated identities |
| Replay resistance | Optional local reference control | SQLite atomic one-time request-ID consumption; database rollback and fresh forged IDs remain possible |
| Delegation attenuation | Not implemented | Cycle rejection only; no capability subset enforcement |
| Evidence ledger | Experimental local format | SHA-256 chain, strict record verification, file flush/fsync; single-writer, no independent checkpoint, no anti-rollback |
| Structural verifier | Implemented | Checks repository artifacts and contract catalog shape; does not execute every JSON Schema keyword or verify deployments |
| Deployment profiles | Specification | No runtime profile verification |
| Unit tests | PASS in CI | 28 tests passed on Python 3.11, 3.12, and 3.13 |
| Structural verifier and JSON syntax | PASS in CI | All three matrix jobs passed |
| CI evidence | PASS | Workflow run 42734201509, tested head aab694b0a58a6ccc741376628498bc9820b88107 |
| Merged implementation | Main | PR #2, merge commit 4a8adac5308e0414018484f68ca4b28d43a053cd |
| Independent review | Not performed | No certification or external audit claim |

## Critical gaps

Authenticated identity and revocation; signed policy provenance and rollback resistance; authenticated request IDs and distributed anti-replay; capability-set delegation attenuation; independent execution broker; complete mediation and bypass testing; OS isolation; independently checkpointed evidence; deployment-level conformance; fuzzing/load/penetration testing; independent security review.

## Validation boundary

The CI PASS applies to the exact tested PR head and workflow. It does not certify the merged deployment, prove a production security boundary, or establish safety. The merge commit contains the same tested source plus GitHub's merge metadata. No independent security review has occurred.
