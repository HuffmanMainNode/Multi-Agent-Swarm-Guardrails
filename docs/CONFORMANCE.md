# Conformance and Assurance

Use PASS, FAIL, UNKNOWN, NOT_TESTED, and NOT_APPLICABLE. Missing evidence is not PASS. Never average results into a score that hides critical failure.

Run `masg verify --root .`. The current verifier checks required repository files and presence/uniqueness of MSC-001 through MSC-010. It reports `repository_structure_only`; it does not test a live deployment or certify any contract.

A future runner must identify implementation/version/profile/configuration/commit; exercise positive, negative, malformed, expiry, replay, partition, and bypass cases; retain attributable integrity-protected evidence; distinguish controls inside the agent process from independently enforced controls; and report skipped/unsupported tests.

Embedded means the host process is trusted. Isolated requires separately protected process/container and authenticated IPC verified in deployment. Hardware-Assured requires fresh independently verified hardware evidence. Never claim a stronger profile than evidence supports. Security Passport signing is not implemented.
