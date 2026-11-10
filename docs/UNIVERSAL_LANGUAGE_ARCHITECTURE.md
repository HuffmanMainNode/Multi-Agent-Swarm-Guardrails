# Universal Human and Machine Language Architecture

## Purpose

MASG is intended to be usable by people and agent systems across languages, operating systems, runtimes, and programming ecosystems. Universal access requires separate solutions for human localization, machine-language implementations, and semantic interoperability. These concerns must not be collapsed into one translation feature.

This document defines an additive architecture. It does not change MASG protocol v1.0.0 authorization semantics.

## Four distinct layers

### 1. Human-language localization

Human-facing labels, guides, errors, and learning material may be localized into any language with a BCP 47 language tag.

- English is the initial authoritative source locale.
- Translation packs are optional, portable files that can be cloned or installed locally.
- Stable message and concept identifiers do not change when wording changes.
- Every translation records its status: untranslated, machine draft, human reviewed, or needs revision.
- Human-reviewed status requires a named reviewer and review timestamp.
- Machine-generated translations are never silently promoted to human-reviewed.
- Missing or unreviewed strings fall back to the source locale.
- Security-critical protocol identifiers, enum values, schema keys, reason codes, and cryptographic inputs are not translated.

### 2. Programming-language implementations

The normative protocol remains language-neutral. Python, Go, Rust, JavaScript/TypeScript, Java, C#, Swift, Kotlin, C, C++, WebAssembly, and future runtimes may implement it.

Each implementation must:
1. Consume the same normative schemas and vectors.
2. Preserve exact protocol semantics and failure behavior.
3. Publish its language/runtime manifest and scoped conformance report.
4. Disclose identity, enforcement, isolation, and deployment limitations.
5. Pass shared tests before it is advertised as conformant.

A language binding is an implementation, not a new protocol. No single SDK is authoritative.

### 3. Semantic interoperability

Different models may tokenize, represent, and reason over information differently. MASG can define a stable external representation for explicit messages, claims, concepts, provenance, and uncertainty without requiring models to share internal architectures.

The experimental Universal Agent Semantic Representation (UASR) is described separately in [AI Semantic Interchange](AI_SEMANTIC_INTERCHANGE.md). It is not part of authorization protocol v1.0.0 and does not expose or standardize private model reasoning.

### 4. Wire and storage efficiency

- JSON remains the inspectable baseline representation.
- Deterministic CBOR is a candidate compact encoding for the same typed data model.
- Binary encoding must preserve the same semantic values and validation constraints.
- Compression must be measured against representative payloads; it must not remove provenance, uncertainty, policy versions, or security-relevant context.
- No custom binary format or canonical signature profile is standardized by this proposal.

## Translation trust model

A translation is content, not authority. A translated instruction, policy label, or explanatory note cannot alter the meaning of a protocol field. Security decisions use stable identifiers and normative semantics, not translated prose.

Review records are evidence about the translation process, not proof that a translation is universally correct. High-impact security and safety terms should receive review by at least two qualified speakers where practical, with disagreements preserved rather than hidden.

## Open-source contribution model

Anyone may:
- Add a language pack.
- Review or correct a translation.
- Implement MASG in another programming language.
- Add a semantic concept or typed frame proposal.
- Publish an independent conformance report.
- Fork the protocol or create a namespaced extension.

Contributions must retain source attribution, license notices, version metadata, and truthful evidence status. No central service or approval authority is required to use a fork or local package.

## Explicit non-goals

This architecture does not:
- Claim perfect machine translation.
- Claim every model understands every language.
- Equate translation with semantic equivalence.
- Standardize hidden chain-of-thought or require disclosure of private model reasoning.
- Make an LLM output authoritative because it is structured or signed.
- Replace established programming languages, JSON, CBOR, Unicode, BCP 47, or mature cryptographic standards.
- Claim that protocol conformance proves safe execution.

## Implementation status

The localization pack schema, English source catalog, and untranslated Spanish template are initial artifacts. No non-English pack is currently certified or marked human reviewed. UASR is an experimental proposal pending review, implementation, and benchmarks.
