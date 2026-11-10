# Changelog

## Unreleased
- Add experimental Linux separate-process execution broker using SO_PEERCRED.
- Derive caller principal from operator-configured OS UID mapping; reject caller-supplied identity and operation fields.
- Expose only the fixed audit.append operation; no shell, arbitrary path, executable, or command support.
- Add bounded broker requests/events, five-minute maximum request lifetime, three-second socket read timeout, and 32-handler cap.
- Add local replay consumption before protected ledger append and fail-closed behavior.
- Add broker CLI serve/append commands, examples, ADR, deployment guidance, and adversarial tests.
- Update architecture, limitations, integration, operations, roadmap, and engineering checkpoint.

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
