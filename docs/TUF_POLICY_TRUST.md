# TUF-Verified Policy Updates

Status: optional experimental policy-source integration using python-tuf 7.x. Static local policy mode remains available and does not authenticate the policy publisher.

## Why TUF

A detached signature can authenticate a file but does not by itself provide a complete secure update workflow. MASG uses The Update Framework (TUF) for the policy update path because its client workflow verifies signed root/targets/snapshot/timestamp metadata, target hashes and lengths, metadata versions, expiration, and delegated trust. MASG does not implement its own signature format or metadata verification.

References:
- [TUF specification](https://theupdateframework.github.io/specification/latest/)
- [python-tuf ngclient Updater API](https://theupdateframework.readthedocs.io/en/latest/api/tuf.ngclient.updater.html)
- [python-tuf installation](https://theupdateframework.readthedocs.io/en/latest/INSTALLATION.html)

## Trust model

1. The adopter provisions a trusted TUF `root.json` bootstrap file out-of-band. Do not fetch the initial trust anchor from the same untrusted mirror it is meant to authenticate.
2. Root metadata defines threshold keys and roles. Use separate role keys and threshold signing appropriate to the deployment. Keep private signing keys offline or in protected signing infrastructure.
3. The mirror contains TUF metadata and target files. It may be a local directory, a copied offline repository, or any operator-managed static mirror. MASG does not host it.
4. The TUF client refreshes metadata and verifies the requested target before MASG loads it as a policy.
5. Any signature, hash, version, expiration, path, cache, or retrieval error prevents broker startup. There is no fallback to an unsigned policy.

## Offline mirror layout

The client expects a TUF repository root with the standard TUF layout:

```text
tuf-mirror/
  metadata/
    timestamp.json
    1.snapshot.json
    1.targets.json
    2.root.json
  targets/
    policies/
      <sha256>.<target-filename>
```

The exact metadata versioned filenames and target hash prefixes are determined by TUF metadata and the repository's consistent-snapshot setting. This tree is illustrative, not a ready-to-trust repository. It contains no private signing keys.

An adopter can clone or copy a signed mirror into an offline environment. The local fetcher accepts only the configured synthetic HTTPS origin and maps requests to files beneath the supplied mirror directory. It does not open network connections.

## Configure the broker

Install the optional integration:

```bash
python -m pip install 'masg-guardrails[tuf]'
```

Provision the following before starting:
- `/etc/masg/trusted-root.json`: out-of-band TUF bootstrap root, protected and read-only to the broker.
- `/srv/masg/tuf-mirror`: operator-managed TUF mirror, not writable by agents or broker.
- `/var/lib/masg/tuf-cache`: persistent, broker-owned TUF metadata and target cache. Do not clear it during normal updates.
- `/etc/masg/principals.json`: protected OS UID-to-principal map.
- `/var/lib/masg/replay.sqlite3` and `/var/lib/masg/evidence.jsonl`: broker-owned state.

Start with TUF policy verification:

```bash
masg broker serve \
  --socket /run/masg/broker.sock \
  --tuf-repository /srv/masg/tuf-mirror \
  --tuf-bootstrap-root /etc/masg/trusted-root.json \
  --tuf-cache /var/lib/masg/tuf-cache \
  --policy-target policies/active.json \
  --principal-map /etc/masg/principals.json \
  --replay-db /var/lib/masg/replay.sqlite3 \
  --ledger /var/lib/masg/evidence.jsonl
```

The policy target defaults to `policies/active.json`. TUF target length is capped at 1 MiB. The policy is then passed through MASG's strict local policy parser.

Static `--policy` and TUF `--tuf-repository` modes are mutually exclusive. TUF mode also requires both the bootstrap root and persistent cache. Missing optional TUF dependencies or invalid metadata cause startup failure.

## Rollback, freeze, and cache assumptions

TUF metadata versions and expiration provide rollback/freeze defenses when the client retains its latest trusted metadata. This requires:
- A persistent metadata cache.
- Cache files and parent directories writable only by the broker service account.
- No restore of an older metadata-cache snapshot without an explicit trust recovery procedure.
- A sufficiently trustworthy system clock for metadata expiration.
- An operator update process that publishes fresh timestamp metadata and rotates keys safely.

If an attacker can roll the cache back to an older trusted state, the client may be made to accept older metadata that has not yet expired. TUF cannot make a compromised local cache rollback-resistant by itself. Use storage/OS controls or an independent monotonic checkpoint if the threat model requires stronger anti-rollback.

Do not run multiple broker instances concurrently against the same TUF metadata cache. python-tuf documents the updater cache as a single-instance resource.

## What this does and does not establish

Established by the TUF library when verification succeeds:
- The target is authorized by the configured TUF trust root and role metadata.
- The target bytes match the signed target metadata.
- Metadata signatures, versions, expiry, and TUF update workflow checks passed.

Not established:
- The policy is wise, safe, lawful, or appropriate.
- The signing keys or root bootstrap were initially provisioned correctly.
- The local cache cannot be rolled back by a privileged attacker.
- The broker host, kernel, clock, policy evaluator, or execution boundary is uncompromised.
- An adopting application routes every protected action through this broker.
- The signing/publishing workflow is implemented by MASG. This repository provides the client integration only; operators must use a TUF-compatible publishing/signing process and protect private keys.

Static policy mode remains useful for local development but does not provide publisher authentication or update rollback protection.
