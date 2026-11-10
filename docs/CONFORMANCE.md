# Conformance and Assurance

Use PASS, FAIL, UNKNOWN, NOT_TESTED, and NOT_APPLICABLE. Missing evidence is not PASS. Never average results into a score that hides critical failure.

Run `masg verify --root .`. The current verifier checks required repository files and presence/uniqueness of MSC-001 through MSC-010. It reports `repository_structure_only`; it does not test a live deployment or certify any contract.

## Universal protocol conformance

The normative language-neutral protocol is in [spec/README.md](../spec/README.md). JSON Schemas are under [schemas/](../schemas/), portable decision vectors and shared raw-parser negative fixtures are under [vectors/v1.0.0/](../vectors/v1.0.0/). Python CI validates the schemas and vectors and executes the decision vectors against the Python reference evaluator. Other language implementations MUST consume the same decision and parser-negative fixtures unchanged and publish their own conformance reports. The parser-negative suite currently covers eighteen malformed-input and timestamp-validation cases across policy and request documents, including impossible calendar dates, clock values, and timezone offsets; it is a baseline, not exhaustive fuzz coverage.

A future full conformance runner must identify implementation/version/profile/configuration/commit; exercise positive, negative, malformed, expiry, replay, partition, and bypass cases; retain attributable integrity-protected evidence; distinguish controls inside the agent process from independently enforced controls; and report skipped/unsupported tests.

## Assurance profiles

Embedded means the host process is trusted. Isolated requires separately protected process/container and authenticated IPC verified in deployment. Hardware-Assured requires fresh independently verified hardware evidence. Never claim a stronger profile than evidence supports. Security Passport signing is not implemented.

Schema validation and vector passes are necessary interoperability evidence, not a security certification. They do not establish identity authenticity, complete mediation, OS isolation, secure recovery, or production readiness.
