# Universal Agent Semantic Representation (UASR)

**Status: Experimental proposal, not a normative MASG v1.0.0 feature.**

## 1. Problem

Agent systems do not share a tokenizer, model architecture, programming language, prompt format, memory model, or orchestration framework. Translating prose between natural languages is not enough to preserve structured meaning, provenance, uncertainty, or constraints.

UASR proposes a small, explicit, typed representation for information that an agent chooses to communicate to another system. It is an interchange format, not a claim about how models internally think.

## 2. Design goals

1. Stable concept identifiers independent of human wording.
2. Typed claims with explicit subject, predicate, and object.
3. Explicit epistemic status so observation, verification, inference, hypothesis, proposal, dispute, and unknown are not conflated.
4. Provenance describing who or what supplied a claim and from which source.
5. Optional evidence references and confidence values, with no implication that confidence is calibrated.
6. Locale metadata for human-readable labels without changing identifiers.
7. Deterministic validation and portable test fixtures.
8. Multiple independent implementations and replaceable encodings.
9. Bounded input size, nesting, claim count, and string lengths.
10. No dependency on a central MASG service.

## 3. Core frame

The initial JSON schema is `schemas/semantic-frame.schema.json`; an illustrative message is in `examples/semantic-frame.example.json`.

A frame contains:
- A schema version and unique frame ID.
- Creation time and BCP 47 locale.
- A declared intent such as ASSERTION, QUESTION, PROPOSAL, or RESULT.
- One or more typed claims.
- Provenance for the producer and source type.

Each claim contains stable subject and predicate concept IDs, a value, and an epistemic status:
- OBSERVED
- VERIFIED
- INFERRED
- HYPOTHESIS
- PROPOSED
- UNKNOWN
- DISPUTED

A VERIFIED claim must include at least one evidence reference. An evidence reference identifies material to inspect; it does not prove that the referenced material is authentic, sufficient, or correctly interpreted. Confidence is optional and is not a universal probability or permission score.

## 4. Stable concepts, localized labels

Concept identifiers are protocol-neutral identifiers such as `masg.authorization.deny_by_default`. A receiving system can resolve a concept through the glossary even if it does not read English.

Human labels and descriptions live in locale packs. They are presentation metadata. They must never replace or modify the stable identifier, a schema key, an enum, a reason code, or a security decision.

Unknown concepts must remain explicitly unknown. A receiver must not silently map an unfamiliar concept to a nearby but different concept.

## 5. Candidate encodings

### JSON

JSON is the initial canonical inspection format because it is widely supported, debuggable, and easy to validate. MASG does not currently define signed JSON envelopes or canonical JSON signature bytes.

### Deterministic CBOR

Deterministic CBOR is a candidate compact representation of the same typed data model. Before adoption, the project must specify:
- Exact CBOR data model and deterministic encoding profile.
- Integer and text key mapping, if numeric keys are used.
- Duplicate/unknown field behavior.
- Maximum bytes, nesting, array sizes, and string lengths.
- Cross-language round-trip vectors.
- JSON-to-CBOR semantic equivalence tests.
- Version negotiation and downgrade behavior.

Do not invent a new binary encoding until benchmarks show an unmet need.

## 6. Efficiency must be measured

Compare JSON, deterministic CBOR, and any later candidate against representative agent messages. Measure:
- Serialized bytes.
- Token counts under multiple unrelated tokenizers.
- Encode/decode latency.
- Memory use.
- Semantic round-trip fidelity.
- Error detection and rejection behavior.
- Compatibility across independent implementations.

A smaller byte stream is not automatically fewer model tokens. Tokenization varies by model. Compression must never erase evidence references, epistemic status, constraints, or policy context.

## 7. Security boundaries

- A UASR frame is untrusted input until validated and its provenance independently established.
- A model-generated claim is not authorization.
- A signed frame proves only the relevant key-possession/signature claim under its trust model; it does not prove truth.
- Multiple agents repeating the same claim do not create independent evidence when they share model, prompt, source, operator, key, or data lineage.
- A structured instruction cannot override MASG authorization or safety contracts.
- Unknown, malformed, contradictory, or unsupported security-critical fields must fail closed.
- UASR does not authorize execution, delegate capabilities, or prove complete mediation.

## 8. Privacy and reasoning boundaries

UASR describes explicit information selected for external communication. It does not define or require disclosure of hidden chain-of-thought, private scratchpads, internal activations, private memory, or proprietary training data. Systems should exchange concise conclusions, evidence, assumptions, uncertainty, and reproducible artifacts appropriate to their privacy policy.

## 9. Open implementation path

1. Review the schema and threat model.
2. Add shared positive and negative semantic-frame vectors.
3. Implement independent validators in Python, JavaScript/TypeScript, Go, and Rust.
4. Add cross-language differential tests.
5. Add JSON/CBOR equivalence tests only after a CBOR profile is approved.
6. Benchmark multiple payload classes and tokenizers.
7. Publish manifests, conformance reports, limitations, and reproducible results.
8. Consider standardization only after independent implementations and external review.

## 10. Current status

The JSON schema and example are experimental artifacts. There is no production UASR parser, CBOR profile, tokenizer, compiler, natural-language translator, or model adapter yet. No efficiency or semantic-preservation claim is made.
