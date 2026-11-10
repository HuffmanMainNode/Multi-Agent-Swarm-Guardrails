# SPIFFE Workload Identity Integration (Experimental)

Status: optional experimental integration. It is not a SPIRE deployment guide or a production identity certification.

## Design

MASG delegates SVID issuance, workload attestation, JWT signature validation, audience validation, and trust-bundle management to a SPIFFE Workload API implementation such as SPIRE. MASG does not implement custom JWT signature validation or maintain its own trust bundle.

The broker receives a JWT-SVID in the bounded request and calls the Workload API's `ValidateJWTSVID` operation for one operator-configured audience. The validated SPIFFE ID becomes the policy principal. A policy must explicitly authorize that exact identity for `audit.append`; valid identity is not authorization.

The broker performs validation for every request. It does not cache positive identity results. If the Workload API is unavailable, validation fails, the token is malformed, the audience is wrong, or the identity is not authorized by policy, the operation is denied.

The request expiration must not exceed the validated JWT-SVID expiration. This prevents a request timestamp from extending authority beyond the presented credential.

## Dependency

The optional `spiffe` extra pins the community-maintained Hewlett Packard Enterprise `py-spiffe` client at 0.4.0. SPIFFE's own integration documentation lists Python libraries as community libraries rather than officially maintained SPIFFE project SDKs. The current PyPI release page reports no publishing provenance for 0.4.0. This is an explicit supply-chain limitation: review the source, transitive dependencies, release artifacts and provenance before enabling this extra in a sensitive deployment. MASG does not silently install it in the base package.

Sources:
- [SPIFFE Workload API](https://github.com/spiffe/spiffe/blob/main/standards/SPIFFE_Workload_API.md)
- [SPIFFE Workload API proto](https://github.com/spiffe/spiffe/blob/main/standards/workloadapi.proto)
- [SPIFFE Python library usage notes](https://spiffe.io/docs/latest/spire-integrations/using/libraries/)
- [py-spiffe source](https://github.com/HewlettPackard/py-spiffe)
- [PyPI release metadata](https://pypi.org/project/spiffe/0.4.0/)

## Configure

Install the optional dependency:

```bash
python -m pip install 'masg-guardrails[spiffe]'
```

Configure the SPIRE Agent or another conformant Workload API implementation to expose a local Unix socket. The broker process must be permitted to access that endpoint. Supply the absolute socket path and a dedicated exact audience. Wildcard, padded, or whitespace-containing audience values are rejected. The socket must be a real Unix socket reached only through normalized absolute path components. Symlinked path components and non-sticky group/world-writable ancestor directories are rejected:

```bash
masg broker serve \\
  --socket /run/masg/broker.sock \\
  --policy /etc/masg/broker-policy.json \\
  --spiffe-endpoint-socket /run/spire/sockets/agent.sock \\
  --spiffe-audience masg-broker \\
  --replay-db /var/lib/masg/replay.sqlite3 \\
  --ledger /var/lib/masg/evidence.jsonl
```

The UID principal map and SPIFFE identity mode are mutually exclusive. The policy's `principals` values must contain exact SPIFFE IDs, for example `spiffe://example.org/agent/evidence-writer`. Do not authorize an entire trust domain with a broad string prefix.

## Request shape

SPIFFE mode requires one additional field:

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "issued_at": "2026-11-10T12:00:00Z",
  "expires_at": "2026-11-10T12:02:00Z",
  "svid": "<short-lived JWT-SVID>",
  "event": {
    "kind": "execution_observation",
    "details": "A bounded event supplied by the client"
  }
}
```

The broker bounds the token to 8192 ASCII bytes, validates it for the configured audience through the local Workload API, and does not copy it into policy requests or the evidence ledger. The request ID is separately consumed in local SQLite before the side effect. The request expiry must be no later than the JWT-SVID expiry.

## Revocation and freshness

The broker calls `ValidateJWTSVID` for every request, so it does not rely on an identity result cached by MASG. The SPIFFE Workload API is responsible for validating the SVID against its current trust material. Revocation effectiveness depends on the identity provider's key/bundle update propagation and its implementation; MASG does not claim globally instantaneous revocation. JWT-SVIDs are short-lived bearer credentials. Expiration bounds exposure, but does not prevent a stolen token from being replayed before expiry if it has not otherwise been invalidated.

A validation timeout or Workload API failure denies the request. No offline identity fallback is provided in this mode. The broker remains locally deployed and requires no MASG cloud service.

## Security boundaries and limitations

- A JWT-SVID is a bearer token. This integration does not bind it cryptographically to the Unix-domain-socket peer PID/UID or to the originating process. A stolen token can be presented by another local process until it expires or becomes invalid.
- Linux `SO_PEERCRED` remains collected as local transport provenance and defense in depth, but SPIFFE ID is the policy principal in SPIFFE mode.
- The broker trusts the Workload API endpoint and its implementation, SPIRE server/agent configuration, workload attestation selectors, trust domain, signing keys, clock, and local socket access controls. The socket path must not traverse symlinked directories or untrusted writable ancestors. Sticky directories such as /tmp are allowed, but a private temporary child directory is still required.
- The broker does not issue SVIDs, register workloads, administer SPIRE, rotate CA keys, configure federation, or manage trust bundles.
- This mode does not yet implement X.509-SVID mutual TLS or sender-constrained credentials.
- No live SPIRE integration test or deployment conformance test is claimed by the unit tests. CI injects a deterministic fake Workload API client to verify request shaping, fail-closed behavior, bounds, identity derivation, expiry binding, and policy mapping.
- The Python client is a third-party optional dependency with no PyPI provenance recorded for the pinned release. A production adoption should vendor/audit and hash-pin the dependency closure or use a separately verified SDK/runtime.
- Identity does not grant permission. Policy still defaults to DENY and matches exact SPIFFE ID, action, target and scope.

## Next work

1. Add X.509-SVID/mTLS or another sender-constrained identity path to reduce bearer-token theft/replay risk.
2. Test against a real local SPIRE Agent and verify rotation, key removal, wrong audience, provider outage, and workload selector changes.
3. Evaluate and improve the optional Python SDK supply-chain provenance before a production deployment.
4. Add authenticated capability delegation only after identity and revocation semantics are proven.
