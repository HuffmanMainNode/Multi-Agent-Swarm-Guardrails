# Changelog

## Unreleased
- Reject duplicate JSON keys, non-standard numeric constants, unknown fields, malformed selectors, and oversized policy/request inputs.
- Require strict timezone-aware RFC3339 timestamps and reject naive evaluation clocks.
- Add optional atomic SQLite request-ID consumption and fail-closed replay-store errors.
- Add concurrent replay tests and replay persistence tests.
- Harden evidence-ledger parsing and fsync appended records.
- Expand contract-catalog structural validation and adversarial tamper tests.
- Record second-pass adversarial review findings and explicit residual limitations.

## 0.1.0 foundation
- Ten versioned mandatory safety contract definitions.
- Local Python deny-by-default policy evaluator.
- Local JSONL hash-chain evidence ledger and verifier.
- Repository structural conformance CLI.
- Example policy/request and deployment manifest.
- Unit tests and Python 3.11/3.12/3.13 GitHub Actions workflow.
- Architecture, threat model, contract index, integration, limitations, and recovery guidance.
- Embedded, isolated, and hardware-assured profile specifications.
- Machine-readable discovery metadata, llms.txt, CITATION.cff, and codemeta.json.
- Security, contribution, governance, agent guidance, issue/PR templates, ADRs, and project continuity registers.
