# Operations and Recovery

Adopter guidance; no recovery engine is implemented.

Use separate agent identities, short-lived scoped credentials, reviewed policy changes, pinned dependencies/tool-server versions, restricted filesystem and egress, bounded recursion/retries/cost/time, and evidence storage outside agent write authority.

Restore application data separately from trust state. Do not automatically restore revoked identities, private keys, policy authority, approval state, or trust decisions. Reissue credentials, verify policy, inspect dependencies, and validate evidence before re-enabling protected actions.

A 3-2-1-1-0 backup pattern may be appropriate: multiple copies, storage types, geographic separation, immutable/offline copy, and restoration/integrity checks. Define RPO/RTO per subsystem. Keep private signing keys out of ordinary backups.

Define safe-stop scope and safe state before incidents. Stop may apply to a tool, session, delegation chain, agent, node, or swarm segment. Preserve evidence and prevent restart evasion. For physical systems, domain engineers must design the safe state; abrupt termination can itself be hazardous.
