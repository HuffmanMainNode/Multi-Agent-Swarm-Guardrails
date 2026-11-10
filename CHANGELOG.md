# Changelog

## Unreleased
- Record PR #16 merged and post-merge main CI success; Go reference v0.1.1 now reports eight shared policy-decision/time vectors with explicit embedded-only scope.
- Record passing cross-language protocol parity CI for complete Python and Go request envelopes, strict raw JSON parsing, schema-aligned limits, Unicode code-point handling, timestamp rules and JSON depth boundary tests.
- Add a strict Python `evaluate_protocol_json` entry point mirroring Go raw-JSON parsing, including duplicate-key, invalid UTF-8, non-standard constant, nesting-depth and byte-limit rejection.
- Align Python and Go policy constraints with the normative schema: required rule IDs, 1,000-rule cap, 128-entry selector cap, field-specific string limits and Unicode code-point counting.
- Add a Python full-envelope protocol evaluator so shared vectors exercise the same v1.0.0 request envelope as Go rather than a stripped internal request.
- Standardize RFC 3339 timestamp precision at six fractional digits and reject unknown local offset `-00:00`; bound policy/request JSON input sizes consistently.
- Add cross-language regression tests for full-envelope requirements, provenance references, Unicode boundaries and timestamp edge cases.
- Align Python and Go policy constraints with the normative schema: required rule IDs, 1,000-rule cap, 128-entry selector cap, field-specific string limits and Unicode code-point counting.
- Add a Python full-envelope protocol evaluator so shared vectors exercise the same v1.0.0 request envelope as Go rather than a stripped internal request.
- Standardize RFC 3339 timestamp precision at six fractional digits and reject unknown local offset `-00:00`; bound policy/request JSON input sizes consistently.
- Add cross-language regression tests for full-envelope requirements, provenance references, Unicode boundaries and timestamp edge cases.
- Define a namespaced extension package model so independent communities can adapt MASG to domains, transports, identity providers, policy engines, enforcement, evidence, and recovery without silently changing core semantics.
- Add an extension manifest schema and generic tool-action mapping example, explicitly marked as documentation-only and not a working adapter.
- Add an independent Go reference evaluator using only the Go standard library; it consumes the shared v1.0.0 decision vectors without a Python dependency and publishes an explicit embedded-only limitation/conformance manifest.
- Add Go CI vet/race-test job and validate the Go implementation manifest and conformance report against the normative schemas.
- Define language-neutral MASG protocol v1.0.0 with JSON Schemas for policies, authorization requests/responses, implementation manifests, conformance reports, and portable conformance vectors.
- Add shared decision vectors and Python CI validation; publish implementation guidance for independent language/runtime adapters.
- Clarify that Python is a reference implementation, not the normative protocol or a required dependency.

- Add optional SPIFFE JWT-SVID validation through the local Workload API for the Linux broker. Validated SPIFFE IDs become exact policy principals; legacy UID mapping remains available.
- Add per-request online validation, bounded bearer-token input, explicit audience configuration, fail-closed provider errors, request-expiry binding to SVID expiry, and tests with an injected Workload API client.
- Document py-spiffe 0.4.0 provenance caveat, bearer-token limitations, and outstanding live SPIRE/X.509-SVID work.
- Merge optional SPIFFE JWT-SVID workload identity integration in PR #8; post-merge main CI run 42744955882 passed 75 tests on each supported Python version.
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
- Validate the TUF client on python-tuf 7.0.1: 57 tests passed per Python 3.11/3.12/3.13 job, with Ruff, structural verification, and JSON checks.
- Merge TUF policy trust integration in PR #6; main-branch CI run 42737605525 passed all three runtimes.

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
