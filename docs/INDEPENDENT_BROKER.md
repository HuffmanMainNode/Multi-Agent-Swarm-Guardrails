# Independent Execution Broker (Experimental Linux Reference)

Status: experimental, Linux-only reference implementation. This document describes the current code, not a certification.

## What it does

The broker is a separate OS process. It exposes exactly one operation:

- `audit.append`
- fixed target: `audit-ledger`
- fixed scope: `append`

A client sends a bounded JSON request containing only a request ID, issue/expiry timestamps, and an event with `kind` and `details`. The client cannot choose a principal, operation, target, scope, file path, executable, or command.

The broker:
1. Obtains the connecting process UID using Linux `SO_PEERCRED`.
2. Maps that UID to a configured MASG principal.
3. Constructs the authorization request itself. It does not trust a principal supplied by the client.
4. Evaluates the operator-controlled deny-by-default policy.
5. Rejects request validity windows longer than five minutes.
6. Atomically consumes the request ID in local SQLite.
7. Appends a bounded event to the broker-owned JSONL ledger.
8. Returns ALLOW only after the append call completes.

Unknown UIDs, malformed requests, denied policy, replay-store errors, replay, and ledger errors do not return ALLOW. If the ledger append fails after replay consumption, the request remains consumed. Operators must inspect the ledger before any retry or recovery.

## What it does not do

- It is not a general tool execution engine, shell, filesystem proxy, or arbitrary command runner.
- It does not authenticate an agent cryptographically or establish identity beyond the local OS UID.
- It does not distinguish two agents running under the same OS UID.
- It does not protect against root, the broker service account, a compromised host kernel, or an attacker who can alter broker-owned state.
- It does not sign policy, prevent policy rollback, or provide distributed revocation/replay.
- It does not guarantee that every other application side effect uses the broker.
- It does not provide a portable Windows/macOS broker. This reference requires Linux `SO_PEERCRED`.
- It is not a sandbox. The broker's own process and filesystem permissions must be configured by the operator.

## Files and ownership

Use a dedicated broker service account and distinct OS identities for agent workloads. Do not run untrusted agents under the broker UID.

Recommended ownership model:
- Policy and UID-to-principal map: root-owned, readable by broker, not writable by broker or agents.
- Broker socket directory: operator-created, not writable by agents; traversable by the client group.
- Socket: broker-owned, group-readable/writable only by the designated client group (mode 0660).
- Replay database and evidence directory: writable only by the broker service account.
- Agent identities: separate OS UIDs. A shared UID collapses all those agents into one OS identity.

The broker rejects symlink/special policy and principal-map files and group/world-writable configuration files. The operator must still protect parent directories against replacement and mount manipulation.

## Configuration

Example policy (replace the principal with the one mapped to the agent's OS UID):

```json
{
  "version": "broker-policy-v1",
  "default_effect": "DENY",
  "rules": [{
    "id": "agent-may-append-evidence",
    "principals": ["agent:evidence-writer"],
    "actions": ["audit.append"],
    "targets": ["audit-ledger"],
    "scopes": ["append"],
    "effect": "ALLOW"
  }]
}
```

Example principal map, where `1001` must be replaced with the actual dedicated agent UID:

```json
{"1001": "agent:evidence-writer"}
```

Both files must be regular files and must not be group-writable or world-writable. Keep them in operator-controlled directories. Restart the broker to load a reviewed policy change.

## Start the broker

Create the socket parent directory first and ensure it is operator-controlled. The broker intentionally refuses to delete or replace an existing socket path automatically.

```bash
install -d -m 0750 -o masg-broker -g masg-clients /run/masg
install -d -m 0700 -o masg-broker -g masg-broker /var/lib/masg
masg broker serve \
  --socket /run/masg/broker.sock \
  --policy /etc/masg/broker-policy.json \
  --principal-map /etc/masg/principals.json \
  --replay-db /var/lib/masg/replay.sqlite3 \
  --ledger /var/lib/masg/evidence.jsonl
```

Run the broker under its dedicated service account, not as an agent and preferably not as root. Arrange the process primary group as the designated client group so the socket's 0660 mode grants access only to that group. The broker service account must be able to read the root-managed configuration files and write only its state directory and runtime socket directory.

## Client request

The request intentionally has no principal, action, target, scope, or path:

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "issued_at": "2026-11-10T12:00:00Z",
  "expires_at": "2026-11-10T12:02:00Z",
  "event": {
    "kind": "execution_observation",
    "details": "A bounded event supplied by the client"
  }
}
```

Submit it:

```bash
masg broker append --socket /run/masg/broker.sock --request request.json
```

The request ID must be unique. The broker's five-minute maximum validity window is an additional bound, not a substitute for trusted time or authenticated message provenance.

## Operational failure behavior

- Policy denial: no replay entry and no ledger append.
- Unknown UID: no policy evaluation and no ledger append.
- Replay-store failure: deny, no ledger append.
- Repeated request ID: deny, no second ledger append.
- Ledger append failure: deny, request ID remains consumed; inspect state before operator-directed recovery.
- Existing socket path: startup refuses; inspect it and remove a stale socket manually only after confirming no broker owns it.
- More than 32 concurrent connections: excess connections are dropped rather than spawning unbounded handler threads.
- Client that does not complete a request within the socket read timeout is dropped.

## Security interpretation

This is a useful protected-operation boundary only when OS identities, socket directory, broker account, policy files, replay database, and ledger ownership are correctly separated. A same-UID malicious process can impersonate any other process with that UID for this broker. A client allowed to connect can submit arbitrary bounded audit content, so do not put secrets or personal data in event details.

This first broker proves one narrow pattern: derive local caller identity from the OS, authorize a fixed operation in a separate process, consume a request ID, and perform a broker-owned side effect. It does not yet provide a general protected executor for arbitrary tools.
