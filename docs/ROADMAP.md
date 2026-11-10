# Roadmap

Priorities are ordered by security dependency, not feature count.

## Experimental foundation
- [x] Ten versioned mandatory safety contracts.
- [x] Deny-by-default local policy evaluator.
- [x] Optional local SQLite replay consumption.
- [x] Local hash-chain evidence ledger.
- [x] Repository structural verifier and CI.
- [x] Experimental Linux separate-process broker for one fixed audit append operation.

## Critical engineering
1. [x] Optional SPIFFE JWT-SVID validation through local Workload API merged in PR #8. Remaining: live SPIRE interoperability/rotation/revocation tests and sender-constrained X.509-SVID/mTLS.
2. [x] Optional TUF policy client verifies signatures, metadata versions/expiry, snapshots, and target hashes from a local mirror. Remaining: repository publishing/signing workflow and independently protected rollback-resistant cache.
3. Cryptographically bound capability delegation with strict attenuation.
4. Typed protected-executor interface and explicit capability registry; no arbitrary shell execution.
5. Expand broker operation-by-operation only after threat model, allowlist, resource limits, authorization, evidence, and bypass tests exist.
6. Independent evidence checkpoint and signed portable evidence format.
7. Deployment-level conformance, property-based/fuzz testing, load testing, and external review.

## Universal protocol and language interoperability
- [x] Publish language-neutral MASG v1.0.0 schemas and eight shared policy/time vectors.
- [x] Python reference evaluator.
- [x] Independent Go standard-library evaluator with race-enabled CI.
- [x] Independent Rust standard-library evaluator with formatting, Clippy and tests.
- [x] Independent JavaScript evaluator with TypeScript declarations and Node.js 22 CI.
- [x] Validate Go, Rust, and JavaScript implementation manifests/reports against normative schemas in Python CI.
- [x] Add eighteen shared malformed-input and RFC 3339 timestamp-validation fixtures consumed unchanged by Python, Go, Rust, and JavaScript.
- [ ] Add cross-language differential/property-based testing and fuzz campaigns.
- [ ] Add framework-specific JavaScript/TypeScript integration adapters after identity and enforcement mappings are defined.
- [ ] Add a portable CLI conformance runner that can validate any implementation report offline.
- [ ] Add a real transport adapter (MCP candidate) only after identity and bypass contracts are defined.

## Interoperability
- ACS/MCP integration only after security contract mappings and compatibility tests.
- A2A identity, audience, expiry, and replay integration.
- OPA/Cedar adapters where they improve interoperability without replacing MASG contracts.

## Release gate
No production or certification claim until identity, policy integrity, execution isolation, complete declared-path mediation, evidence trust, recovery, and independent review are tested in a documented threat model.

## Human-language and AI semantic interoperability

- [x] Define portable BCP 47 translation-pack schema with explicit UNTRANSLATED, MACHINE_DRAFT, HUMAN_REVIEWED, and NEEDS_REVISION states.
- [x] Publish authoritative English message catalog and an explicitly untranslated Spanish contributor template.
- [x] Publish stable multilingual concept identifiers and English glossary definitions.
- [x] Publish experimental UASR semantic-frame schema with explicit epistemic status and evidence requirement for VERIFIED claims.
- [ ] Add shared positive/negative semantic-frame vectors and translation-pack conformance vectors.
- [ ] Add independent localization and semantic-frame validators in Python, JavaScript/TypeScript, Go, and Rust.
- [ ] Build a contributor review workflow for security-critical translations, including source-change invalidation and reviewer metadata checks.
- [ ] Benchmark JSON against deterministic CBOR for bytes, model-token counts across multiple tokenizers, encode/decode latency, and semantic round-trip fidelity.
- [ ] Approve a compact binary profile only after independent implementations, benchmark evidence, and external review.
- [ ] Expand independent protocol implementations to Java, C#, Swift, Kotlin, C/C++, and WebAssembly as community demand and maintainers allow.

UASR is experimental and separate from authorization protocol v1.0.0. No hidden-reasoning disclosure, translation accuracy guarantee, or token-efficiency result is claimed.

- [x] Add Python and JavaScript/TypeScript template generators that create untranslated packs for any syntactically valid locale tag.
- [x] Add a schema and uniqueness checks for the controlled contextual glossary of protocol and security terms.
- [ ] Add Go and Rust template generators with matching behavior.

## Universal access and learning

- [x] Publish a no-install, no-code first lesson using existing request and policy examples.
- [x] Publish learning paths from first computer concepts through independent implementation.
- [x] Publish a plain-language computing/protocol glossary and safe AI collaboration guide.
- [ ] Add reviewed translations of the beginner entry points, beginning with community-selected languages; keep machine drafts visibly unreviewed.
- [ ] Add accessible, low-bandwidth, mobile-aware learning examples and text alternatives for visual material.
- [ ] Add a browser-based, optional, sandboxed practice environment only after its threat model, isolation, data handling, and maintenance costs are reviewed. It must not be required to use the repository.
- [ ] Create small, independently checkable exercises for JSON, schemas, test vectors, localization, and semantic frames.
- [ ] Invite novice usability testing and publish what confused participants and what was changed.
