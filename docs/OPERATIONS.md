# Operations and Recovery

Adopter guidance; no recovery engine is implemented.

Use separate agent identities, short-lived scoped credentials, reviewed policy changes, pinned dependencies/tool-server versions, restricted filesystem and egress, bounded recursion/retries/cost/time, and evidence storage outside agent write authority.

For the experimental Linux broker:
- Run it under a dedicated non-root service account.
- Run each agent under a distinct OS UID when distinct authority is required.
- Keep policy and UID map root-managed and non-writable by agents or the broker service.
- Keep replay DB and evidence directory writable only by the broker service account.
- Put the Unix socket in an operator-controlled directory. Grant socket group access only to intended client workloads.
- Do not expose the broker socket through a network proxy or mount it into unrelated containers.
- Keep broker configuration and state on protected local storage. The local replay DB is not rollback-resistant.
- Inspect the evidence ledger after any append failure; the request ID remains consumed.

Restore application data separately from trust state. Do not automatically restore revoked identities, private keys, policy authority, approval state, or trust decisions. Reissue credentials, verify policy, inspect dependencies, and validate evidence before re-enabling protected actions.

A 3-2-1-1-0 backup pattern may be appropriate: multiple copies, storage types, geographic separation, immutable/offline copy, and restoration/integrity checks. Define RPO/RTO per subsystem. Keep private signing keys out of ordinary backups.

Define safe-stop scope and safe state before incidents. Stop may apply to a tool, session, delegation chain, agent, node, or swarm segment. Preserve evidence and prevent restart evasion. For physical systems, domain engineers must design the safe state; abrupt termination can itself be hazardous.
