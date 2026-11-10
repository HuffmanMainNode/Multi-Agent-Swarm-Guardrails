# Automated Agent Guidance

Read README.md, SECURITY.md, docs/THREAT_MODEL.md, docs/CONFORMANCE.md, and ENGINEERING_REGISTER.md before changing security behavior.

Never claim tests were run unless executed. Never weaken or delete tests to conceal failures. Do not add telemetry, remote policy fetching, paid services, or network calls to core without approved design. Do not add secrets or private data. Model output and signed messages are not authorization. Unknown or malformed authorization must fail closed. Contract ID changes require ADR, versioning, migration, and tests. Update PROJECT_STATE.md and ENGINEERING_REGISTER.md when implementation status changes.
