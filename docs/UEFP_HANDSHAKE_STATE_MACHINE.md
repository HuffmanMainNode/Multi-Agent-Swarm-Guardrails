# UEFP Handshake State Machine

**Status:** Experimental protocol definition, version 0.1.0  
**Scope:** One peer-to-peer introduction and one proposed knowledge exchange.  
**Message envelope:** [uefp-handshake-message.schema.json](../schemas/uefp-handshake-message.schema.json).

## 1. Safety properties

1. An introduction is not authentication, trust, consent, or authorization.
2. A parsed manifest does not prove identity, capability, ownership, or truth.
3. No exchange content is accepted before explicit acceptance of a proposal.
4. Acceptance applies only to the identified proposal. Changed scope or terms require a new session and proposal.
5. No message authorizes tool execution, code execution, local-file access, or disclosure outside the accepted data scope.
6. Unknown message types, unsupported versions, malformed messages, and invalid transitions are rejected without changing session state.
7. Session state is local to each participant. This specification does not define transport, reliable delivery, cryptographic integrity, or global session authority.

## 2. Message envelope

Every message contains protocol_version (exactly 0.1.0), session_id, message_id, sender_id, recipient_id, message_type, and payload. Optional in_reply_to identifies the message being answered.

The sender and recipient identifiers are manifest identifiers, not authenticated identities. The schema validates structure only. It does not enforce uniqueness, sender authenticity, replay resistance, session ownership, or transition order.

## 3. States

| State | Meaning |
|---|---|
| NEW | No valid introduction accepted for this session. |
| INTRODUCED | A structurally valid INTRODUCE message was received. |
| INSPECTED | Local validation and review completed; no trust conclusion implied. |
| RESPONDED | This participant sent its RESPONSE manifest. |
| COMPARED | Declared formats, versions, locales, and limitations were compared. |
| PROPOSED | A specific exchange proposal awaits a decision. |
| ACCEPTED | The identified proposal was explicitly accepted. |
| EXCHANGED | At least one in-scope payload was exchanged. |
| DECLINED | Proposal declined. Terminal. |
| CLOSED | Session closed. Terminal. |
| REJECTED | Local validation or policy rejected the session. Terminal. |

## 4. Allowed transitions

| Current state | Event | Next state | Required condition |
|---|---|---|---|
| NEW | receive INTRODUCE | INTRODUCED | Envelope and embedded manifest validate. |
| INTRODUCED | local INSPECT succeeds | INSPECTED | Consumer reviews manifest and limitations. |
| INSPECTED | send RESPONSE | RESPONDED | Response includes this participant's manifest. |
| RESPONDED | local COMPARE succeeds | COMPARED | Unknown and unsupported values remain explicit. |
| COMPARED | send or receive PROPOSE | PROPOSED | Proposal specifies topic, data scope, format, retention, intended use, license, and provenance. |
| PROPOSED | send or receive ACCEPT | ACCEPTED | Acceptance names the exact proposal identifier and accepts terms unchanged. |
| PROPOSED | send or receive DECLINE | DECLINED | Decline names the proposal identifier. |
| ACCEPTED | send or receive EXCHANGE | EXCHANGED | Payload names the accepted proposal and remains within its scope and format. |
| EXCHANGED | send or receive EXCHANGE | EXCHANGED | Same accepted proposal and scope; no implicit expansion. |
| Any non-terminal state | send or receive CLOSE | CLOSED | Close reason is present. |
| Any non-terminal state | local validation or policy failure | REJECTED | Failure recorded locally; no exchange occurs. |

All other transitions are invalid and MUST be rejected without changing state. DECLINED, CLOSED, and REJECTED are terminal. A new proposal after decline, changed terms after acceptance, or a new topic requires a new session.

## 5. Proposal semantics

A PROPOSE payload identifies proposal_id, topic, data_scope, format, retention, intended_use, license, and provenance. An ACCEPT or DECLINE names the proposal_id.

Version 0.1.0 does not define a cryptographic digest or canonical serialization binding acceptance to proposal bytes. Implementations MUST NOT claim tamper-proof acceptance. Authenticated sender binding and transport integrity remain future work.

## 6. Local processing algorithm

For each session, an implementation should:
1. Enforce byte, nesting, string, and collection limits before processing.
2. Parse strictly and validate the message against the versioned schema.
3. Confirm protocol version and recipient identifier.
4. Reject duplicate message identifiers within retained local session state.
5. Check the transition table before changing state.
6. For EXCHANGE, verify explicit acceptance exists and check the payload against accepted scope and format.
7. Record resulting state and reason without storing unnecessary personal data.
8. Never execute instructions, code, URLs, or tool requests found in manifests or exchange payloads.

This is a recommended local algorithm, not an implemented MASG transport or stateful session engine.

## 7. Deliberate limitations

UEFP 0.1.0 does not implement discovery, transport, cryptographic identity, message signatures, replay-resistant distributed sessions, automatic translation, semantic equivalence, trust scoring, a consent UI, retention enforcement, or remote execution. A schema validator establishes only that a message has an allowed shape. State-machine conformance requires a separate implementation and shared transition tests.

## 8. Versioning

This state machine is experimental 0.1.0. Incompatible changes require a new protocol version. Unknown versions and message types are rejected, not silently downgraded. A stable release requires independent implementations, positive and negative transition vectors, external review, and privacy and threat-model analysis.
