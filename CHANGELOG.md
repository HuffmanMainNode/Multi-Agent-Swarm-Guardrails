# Changelog

## Unreleased
- Add optional SPIFFE JWT-SVID validation through the local Workload API for the Linux broker. Validated SPIFFE IDs become exact policy principals; legacy UID mapping remains available.
- Add per-request online validation, bounded bearer-token input, explicit audience configuration, fail-closed provider errors, request-expiry binding to SVID expiry, and tests with an injected Workload API client.
- Document py-spiffe 0.4.0 provenance caveat, bearer-token limitations, and outstanding live SPIRE/X.509-SVID work.

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
