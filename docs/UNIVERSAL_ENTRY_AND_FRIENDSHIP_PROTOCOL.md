# Universal Entry and Friendship Protocol (UEFP)

**Status: Experimental design proposal, version 0.1.0. Not a normative MASG security or authorization feature.**

## 1. Purpose

UEFP is a proposed open format for independent people-operated systems, software projects, and AI agents to introduce themselves, describe how they can communicate, state what they can and cannot do, and propose a bounded knowledge exchange.

The design goal is connection without forced conformity. Participants should not need to adopt one programming language, operating system, model, vendor, country-specific workflow, or centralized service to participate.

"How do you do it? Here is how we do it, and what we learned" is the intended spirit of the exchange.

UEFP is not a social network, identity provider, global directory, trust authority, automatic translator, or remote execution protocol.

## 2. Design principles

1. **Open participation:** A participant can publish a manifest, inspect another manifest, or exchange a message without registering with a MASG-operated service.
2. **Local-first:** Discovery and validation work from local files. Network discovery is optional and transport-specific.
3. **Plural implementations:** Systems may use different languages, operating systems, models, and architectures.
4. **Identity without forced identity provider:** A manifest identifier is a label, not proof of identity. Authentication is a separate, optional mechanism defined by a deployment.
5. **Consent before exchange:** A participant must explicitly accept a proposed exchange. An introduction is not consent.
6. **Capabilities are declarations:** A manifest describes claimed capabilities; it does not prove them.
7. **No implied authority:** Discovery, compatibility, handshake completion, or friendly status never grants permission to execute tools, access data, delegate authority, or change policy.
8. **Meaning before translation:** Stable identifiers and typed fields remain stable. Human-readable labels can be localized without changing protocol meaning.
9. **Honest uncertainty:** Unknown, unsupported, untested, and unreviewed values remain explicit.
10. **No forced centralization:** Public Git repositories and independent mirrors may distribute specifications, templates, and implementations. No central registry is required.

## 3. Participant types

The initial model recognizes:
- HUMAN: a person participating directly or through an interface.
- SOFTWARE: an application, service, library, or operating system component.
- AI_AGENT: an AI-enabled agent or assistant.
- ORGANIZATION: a group or institution publishing a participation profile.

A participant may be operated by another participant. The manifest does not establish legal identity, ownership, or authority.

## 4. Introduction manifest

The experimental JSON Schema is [participant-manifest.schema.json](../schemas/participant-manifest.schema.json). The example is [participant-manifest.example.json](../examples/participant-manifest.example.json). The 0.1.0 message envelope is defined in [uefp-handshake-message.schema.json](../schemas/uefp-handshake-message.schema.json).

The manifest can describe:
- A stable, locally chosen participant identifier.
- Participant type and optional display name.
- A short self-description.
- Supported UEFP protocol versions.
- Human languages using locale tags.
- Message and data formats.
- Declared capabilities and limitations.
- A consent posture for proposed exchanges.
- Optional public documentation links.

The manifest must not contain secrets, private credentials, personal data that the participant does not intend to publish, or hidden system prompts. Implementations should allow participants to omit optional fields.

A participant identifier is not a verified identity. A capability declaration is not evidence of capability. A documentation link is untrusted external content.

## 5. Friendship handshake

A minimal conceptual exchange has these steps:

1. **INTRODUCE:** Participant A shares a manifest.
2. **INSPECT:** Participant B validates its syntax, reads its limitations, and decides whether to continue.
3. **RESPOND:** Participant B shares its own manifest or a bounded response.
4. **COMPARE:** Participants identify common message formats, locales, and declared capabilities. Unknown or incompatible fields remain unknown or incompatible.
5. **PROPOSE:** One participant proposes a specific knowledge exchange, including topic, data boundaries, format, retention expectations, and intended use.
6. **CONSENT:** The other participant explicitly accepts, declines, or requests changes.
7. **EXCHANGE:** Only the accepted content is shared over a separately selected transport.
8. **CLOSE:** Participants record completion or termination according to their own policies.

The message envelope and local session transitions are specified in [UEFP Handshake State Machine](UEFP_HANDSHAKE_STATE_MACHINE.md). This remains an experimental protocol definition, not an implemented network handshake or stateful session engine. The repository does not provide a transport, discovery server, cryptographic identity system, or automated consent manager.

## 6. Trust is not friendship

UEFP deliberately separates these concepts:

- **Introduced:** a manifest was received.
- **Parsed:** its syntax passed a validator.
- **Compatible:** declared formats or protocol versions overlap.
- **Authenticated:** an independent identity mechanism verified a credential under a stated trust model.
- **Trusted:** a local operator or policy assigned a trust decision.
- **Consented:** a participant accepted a specific proposed exchange.
- **Authorized:** a separate policy system permitted a specific action.
- **Executed:** a system performed an operation and produced independently inspectable evidence.

None of these states implies the next. In particular, a friendly response does not authenticate a participant, and a successful handshake does not authorize execution.

## 7. Knowledge exchange

A knowledge exchange should carry enough context for another participant to assess and reuse the material:
- The question or problem being addressed.
- The environment and constraints where the approach was used.
- The method and relevant implementation details.
- Observed results and how they were measured.
- Known failures, trade-offs, and limitations.
- Provenance, license, and attribution.
- Whether the content is observed, verified, inferred, proposed, unknown, or disputed.

Use UASR semantic frames as an experimental optional representation where appropriate. Do not require them for participation. Plain text, Markdown, code, and JSON remain valid exchange materials when their meaning and licensing are clear.

Knowledge should not be silently rewritten as universal truth. Preserve regional context and alternative approaches.

## 8. Language and culture

- Locale tags describe language/region preferences; they do not prove fluency.
- Translation quality must not be inferred from a machine-generated label.
- Machine translations remain drafts until reviewed by a competent human.
- Keep identifiers, schema keys, enum values, and security-sensitive reason codes stable.
- Allow multiple regional terms and explanations where one-to-one translation would distort meaning.
- Ask participants how they describe their own practices rather than assuming one country's workflow is universal.

## 9. Security and privacy requirements

Consumers must:
- Treat received manifests and links as untrusted input.
- Apply size, nesting, string-length, and parsing limits.
- Never automatically execute code or follow arbitrary instructions in a manifest.
- Never fetch arbitrary URLs without a separate safe retrieval policy.
- Avoid leaking local environment details during discovery.
- Request consent before sharing non-public data.
- Use separate authentication and authorization controls for sensitive exchanges.
- Keep credentials and secrets out of manifests and public examples.
- Record provenance without collecting unnecessary personal information.

A manifest can be forged or copied. Schema validation only checks structure. It does not establish truth, identity, capability, safety, or ownership.

## 10. Distribution and discovery

The initial distribution model is intentionally decentralized:
- Public Git repositories for specifications, schemas, examples, and implementations.
- Independent mirrors and downloadable release archives.
- Local files and removable-media transfer for offline environments.
- Optional community directories operated independently, with their own moderation and trust policies.

GitHub is a useful collaboration and distribution point, not a universal network guarantee. Some participants cannot reach it due to network policy, filtering, or connectivity limitations. Mirrors and offline distribution are therefore first-class design considerations.

## 11. Versioning and compatibility

This proposal begins at 0.1.0. Before a stable release, the project needs:
- Normative stabilization and independent review of the experimental message envelope and handshake state machine.
- Shared positive and negative test vectors.
- Independent validators in multiple languages.
- Explicit version negotiation and downgrade behavior.
- A privacy and threat-model review.
- Transport-independent conformance rules.
- External review from contributors in different regions and technical communities.

Unknown protocol versions must not be silently treated as compatible. Implementations should preserve unknown optional metadata where safe and reject unknown security-critical semantics.

## 12. Current limitations

The current repository does not implement:
- Live participant discovery or a global directory.
- A network handshake or message transport.
- Cryptographic participant identity or key management.
- Automatic translation or semantic equivalence.
- Automated consent negotiation.
- Trust scoring or reputation ranking.
- Capability verification.
- Remote execution or authorization through UEFP.

The schema and example are experimental starting points. They are not evidence that independent systems can yet interoperate through UEFP.

## 13. Community invitation

We want to learn how different communities already solve these problems. Contributors are invited to share:
- How their systems introduce themselves.
- What information they need before collaborating.
- How they represent capabilities and limitations.
- How they express consent and trust.
- Which languages and formats they use.
- What breaks when systems from different environments meet.

A useful contribution can be a documented workflow, a translation review, a critique, a test vector, or an independent implementation. No single culture or maintainer should define universality alone.
