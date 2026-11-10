# Interoperability Strategy

Listing a project is an integration target, not a claim of implementation, endorsement, or certification.

| Technology | Intended role | MASG status |
|---|---|---|
| OWASP Agent Control Standard | Guardian/action governance | Research target; no adapter |
| MCP | Tool server and invocation boundary | Design guidance; no adapter |
| A2A | Peer identity, messaging, delegation | Design guidance; no adapter |
| OPA / Cedar | Policy decision integration | Candidate; not implemented |
| SPIFFE/SPIRE | Workload identity | Experimental optional JWT-SVID validation through the local Workload API; no X.509-SVID/mTLS binding or live SPIRE deployment conformance test |
| OpenTelemetry | Trace/evidence correlation | Candidate; not implemented |
| CycloneDX / SPDX | Software and agent inventory | Documentation only |
| TUF | Secure update metadata and policy target verification | Optional experimental python-tuf client for local mirrors; no repository publisher |
| SLSA / in-toto / Sigstore | Build provenance | Candidate; not implemented |
| OS sandbox / containers / gVisor | Process isolation | Adopter responsibility |

Prefer maintained implementations and established protocols. Do not invent bespoke cryptography, identity providers, policy languages, transports, or sandboxes. Integrations require version pinning, threat-model review, compatibility tests, licensing review, and explicit failure behavior.
