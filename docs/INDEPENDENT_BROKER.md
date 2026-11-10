# Independent Execution Broker (Experimental Linux Reference)

Status: experimental, Linux-only reference implementation. This document describes the current code, not a certification.

## What it does

The broker is a separate OS process. It exposes exactly one operation:

- `audit.append`
- fixed target: `audit-ledger`
- fixed scope: `append`

A client sends a bounded JSON request containing a request ID, issue/expiry timestamps, and an event with `kind` and `details`. In legacy UID mode it contains no identity field; in SPIFFE mode it also carries a short-lived JWT-SVID. The client cannot choose an operation, target, scope, file path, executable, or command.

The broker:
1. Obtains the connecting process UID using Linux `SO_PEERCRED` as local transport provenance.
2. In UID mode, maps that UID to an operator-configured MASG principal. In SPIFFE mode, validates the presented JWT-SVID through the local SPIFFE Workload API for a configured audience and derives the principal from its validated SPIFFE ID.
3. Constructs the authorization request itself. It never trusts a client-supplied principal.
4. Evaluates the operator-controlled deny-by-default policy.
5. Rejects request validity windows longer than five minutes and prevents the request from outliving the validated SVID.
6. Atomically consumes the request ID in local SQLite.
7. Appends a bounded event to the broker-owned JSONL ledger without storing the bearer token.
8. Returns ALLOW only after the append call completes.

Unknown identities, malformed requests, denied policy, replay-store errors, replay, Workload API failures, and ledger errors do not return ALLOW. If the ledger append fails after replay consumption, the request remains consumed. Operators must inspect the ledger before any retry or recovery.

## What it does not do

- It is not a general tool execution engine, shell, filesystem proxy, or arbitrary command runner.
- Legacy UID mode does not authenticate an agent cryptographically and does not distinguish two agents sharing a UID.
- Optional SPIFFE mode validates JWT-SVIDs online through the local Workload API. It depends on the Workload API endpoint, its attestation and trust configuration, the broker's ability to access it, and the configured audience. JWT-SVIDs are bearer credentials; this integration does not cryptographically bind a token to the Unix-socket peer process.
- It does not protect against root, the broker service account, a compromised host kernel, or an attacker who can alter broker-owned state.
- Static policy mode does not authenticate policy publishers. Optional TUF mode verifies policy publisher metadata and target bytes; its cache rollback resistance depends on protected persistent storage.
- It does not guarantee that every other application side effect uses the broker.
- It does not provide a portable Windows/macOS broker. This reference requires Linux `SO_PEERCRED`.
- It is not a sandbox. The broker's own process and filesystem permissions must be configured by the operator.

## Files and ownership

Use a dedicated broker service account and distinct OS identities for agent workloads. Do not run untrusted agents under the broker UID.

Recommended ownership model:
- Policy and UID-to-principal map: root-owned, readable by broker, not writable by broker or agents in UID mode.
- Broker socket directory: operator-created, not writable by agents; traversable by the client group.
- Socket: broker-owned, group-readable/writable only by the designated client group (mode 0660).
- Replay database and evidence directory: writable only by the broker service account.
- Agent identities: separate OS UIDs when using UID mode. In SPIFFE mode, assign distinct workload identities and protect Workload API socket access.

The broker rejects symlink/special policy and principal-map files and group/world-writable configuration files. The operator must still protect parent directories against replacement and mount manipulation.

## UID configuration

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

## SPIFFE/SPIRE workload identity mode

Install the optional client dependency with `python -m pip install 'masg-guardrails[spiffe]'`. Configure SPIRE or another SPIFFE Workload API implementation to expose a local Unix socket accessible to the broker. The broker validates every presented JWT-SVID online through `ValidateJWTSVID`, with a fixed audience and a two-second default timeout. The validated SPIFFE ID becomes the policy principal. Write exact SPIFFE IDs into the policy's `principals` selectors. There is no UID-to-principal map in this mode.

```bash
masg broker serve \\
  --socket /run/masg/broker.sock \\
  --policy /etc/masg/broker-policy.json \\
  --spiffe-endpoint-socket /run/spire/sockets/agent.sock \\
  --spiffe-audience masg-broker \\
  --replay-db /var/lib/masg/replay.sqlite3 \\
  --ledger /var/lib/masg/evidence.jsonl
```

A SPIFFE-mode request adds an `svid` field containing the JWT-SVID. The token is bounded, validated for the configured audience on each request, and never written to the evidence ledger. Validation failure or Workload API unavailability fails closed. The request expiry must not exceed the validated SVID expiry. See [SPIFFE Workload Identity](SPIFFE_WORKLOAD_IDENTITY.md) for identity semantics, dependency notes, and limitations.

## TUF-backed policy source

Instead of `--policy`, operators may supply a local TUF mirror and an out-of-band bootstrap root:

```bash
masg broker serve \\
  --socket /run/masg/broker.sock \\
  --tuf-repository /srv/masg/tuf-mirror \\
  --tuf-bootstrap-root /etc/masg/trusted-root.json \\
  --tuf-cache /var/lib/masg/tuf-cache \\
  --policy-target policies/active.json \\
  --principal-map /etc/masg/principals.json \\
  --replay-db /var/lib/masg/replay.sqlite3 \\
  --ledger /var/lib/masg/evidence.jsonl
```

Install the optional dependency with `python -m pip install 'masg-guardrails[tuf]'`. The bootstrap root must be provisioned out-of-band. The TUF metadata cache must persist and be protected against rollback. Only one broker instance may use a given cache at a time. Any TUF verification or retrieval failure prevents startup; the broker never falls back to unsigned policy. See [TUF Policy Trust](TUF_POLICY_TRUST.md) for the trust model, mirror layout, cache assumptions, and limitations.

## Start the UID-mode broker

Create the socket parent directory first and ensure it is operator-controlled. The broker intentionally refuses to delete or replace an existing socket path automatically.

```bash
install -d -m 0750 -o masg-broker -g masg-clients /run/masg
install -d -m 0700 -o masg-broker -g masg-broker /var/lib/masg
masg broker serve \\
  --socket /run/masg/broker.sock \\
  --policy /etc/masg/broker-policy.json \\
  --principal-map /etc/masg/principals.json \\
  --replay-db /var/lib/masg/replay.sqlite3 \\
  --ledger /var/lib/masg/evidence.jsonl
```

Run the broker under its dedicated service account, not as an agent and preferably not as root. Arrange the process primary group as the designated client group so the socket's 0660 mode grants access only to that group. The broker service account must be able to read the root-managed configuration files and write only its state directory and runtime socket directory.

## Client request

The UID-mode request intentionally has no principal, action, target, scope, identity, or path:

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

In SPIFFE mode, add the `svid` field to the request. Obtain a JWT-SVID from the workload's SPIFFE Workload API for the audience configured on the broker. The token is a bearer credential and should be short-lived; the broker validates it on each request and never stores it in evidence.

Submit it:

```bash
masg broker append --socket /run/masg/broker.sock --request request.json
```

The request ID must be a canonical UUID version 4 and unique. Generate one with a cryptographically secure UUIDv4 implementation. UUID format does not authenticate the caller or prevent a malicious authorized caller from minting fresh IDs. The broker's five-minute maximum validity window is an additional bound, not a substitute for trusted time or authenticated message provenance.

## Operational failure behavior

- Policy denial: no replay entry and no ledger append.
- Unknown UID in UID mode: no policy evaluation and no ledger append.
- Invalid, expired, wrong-audience, revoked-key or otherwise untrusted JWT-SVID: no policy evaluation and no ledger append.
- SPIFFE Workload API unavailable: identity validation fails closed; no ledger append.
- Request expiry later than the validated SVID expiry: DENY.
- Replay-store failure: deny, no ledger append.
- Repeated request ID: deny, no second ledger append.
- Ledger append failure: deny, request ID remains consumed; inspect state before operator-directed recovery.
- Existing socket path: startup refuses; inspect it and remove a stale socket manually only after confirming no broker owns it.
- More than 32 concurrent connections: excess connections are dropped rather than spawning unbounded handler threads.
- Client that does not complete a request within the socket read timeout is dropped.

## Security interpretation

This is a useful protected-operation boundary only when OS identities, socket directory, broker account, policy files, replay database, and ledger ownership are correctly separated. A same-UID malicious process can impersonate any other process with that UID in UID mode. In SPIFFE mode, a stolen JWT-SVID remains a bearer credential until expiry or invalidation by the Workload API trust domain; it is not bound to the connecting UID. A client allowed to connect can submit arbitrary bounded audit content, so do not put secrets or personal data in event details.

This first broker proves one narrow pattern: derive local caller identity from the OS or validate a SPIFFE JWT-SVID, authorize a fixed operation in a separate process, consume a request ID, and perform a broker-owned side effect. It does not yet provide a general protected executor for arbitrary tools.
