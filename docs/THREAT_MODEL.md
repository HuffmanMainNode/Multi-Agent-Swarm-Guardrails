# Threat Model

## Assets
Tool credentials, protected data, system policy, identity/delegation authority, model/tool/dependency integrity, memory provenance, action execution, audit evidence, recovery state, approval channels, and availability.

## Threat actors
Compromised or malicious agent; malicious operator; compromised tool or peer; supply-chain attacker; prompt/memory poisoner; Sybil or colluding swarm participant; compromised identity/policy/observability service; infrastructure attacker; insider.

## Abuse cases
1. Prompt injection induces privileged tool use.
2. Tool metadata/schema poisoning changes the apparent action.
3. Low-privilege agent delegates to a peer to escalate privilege.
4. Compromised agent invokes alternate side-effect path around middleware.
5. Revoked identity remains authorized through stale cache.
6. Malicious dependency/update compromises enforcement.
7. Peer message is replayed, redirected, or modified.
8. Correlated agents are misrepresented as independent reviewers.
9. Audit evidence is modified, truncated, reordered, or replaced.
10. Recovery restores poisoned data, credentials, or trust.
11. Denial of service exhausts policy, guardian, or evidence services.
12. High-impact capability is disguised as benign use.

## Principles
Authentication, trust, authorization, and safe execution are separate. A signature proves key possession under cryptographic assumptions, not permission. Multiple agents agreeing is not independent verification if they share model, key, operator, infrastructure, or data lineage. Untrusted content must not create authority even if injection detection fails. Delegated capabilities must be attenuated. Unknown evidence is not PASS. Restore application data separately from trust state.

## Out of scope for current package
Hostile kernel, arbitrary control of host process, compromised interpreter, stolen credentials, malicious firmware, complete network compromise, and attacker able to replace both ledger and trusted checkpoint.
