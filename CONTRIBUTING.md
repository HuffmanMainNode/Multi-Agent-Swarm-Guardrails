# Contributing

Be reproducible and technically candid. Never claim a control is implemented because documentation describes it. Preserve the distinction between model refusal, policy decision, and independently enforced boundary. Do not add telemetry, remote services, paid APIs, or network calls to core without an approved design. Never submit secrets or private data.

Before a PR: read README, SECURITY, threat model, conformance docs, and relevant contract; add tests; run `python -m unittest discover -s tests -v` and `masg verify --root .`; run Ruff if installed; update ENGINEERING_REGISTER and PROJECT_STATE.

Contract IDs are permanent. Breaking normative changes require versioning, migration notes, threat-model review, test vectors, and an ADR. PRs must describe threat, exact behavior, contracts affected, bypass analysis, commands/results, compatibility, and residual limitations.
