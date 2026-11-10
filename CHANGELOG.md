# Changelog

## Unreleased
- Add experimental Linux separate-process execution broker using SO_PEERCRED.
- Derive caller principal from operator-configured OS UID mapping; reject caller-supplied identity and operation fields.
- Expose only the fixed audit.append operation; no shell, arbitrary path, executable, or command support.
- Require canonical UUIDv4 request IDs and reject request lifetimes over five minutes.
- Bound message size, JSON nesting, event details, socket read time, and concurrent handler count.
- Reject symlink/special configuration files and group/world-writable configuration, state, and socket parent directories.
- Add local replay consumption before protected ledger append and fail-closed behavior.
- Add broker CLI serve/append commands, examples, ADR, deployment guidance, and adversarial tests.
- Record broker test results and residual risks; 46 tests passed on each of Python 3.11, 3.12, and 3.13.

- Merge the independent Linux broker in PR #4; main-branch CI passed all 46 tests on Python 3.11, 3.12, and 3.13.

- Add optional python-tuf 7.x policy retrieval from an operator-managed local mirror; verify out-of-band bootstrap root, metadata signatures/versions/expiry, snapshot consistency, and target hashes before broker policy load.
- Add fail-closed TUF broker startup mode, persistent metadata cache requirements, optional dependency extra, TUF adversarial tests, and publishing/operations guidance. Static policy mode remains unauthenticated.

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
