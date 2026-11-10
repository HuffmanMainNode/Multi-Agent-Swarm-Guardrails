# MASG Namespaced Extension Model

## Purpose

MASG has one stable language-neutral core and many replaceable adapters and domain profiles. Extensions let independent communities adapt MASG to their protocols, runtimes, tools, and sectors without rewriting the core or forcing every user onto one language or vendor.

An extension is a separately versioned package of mappings, schemas, vectors, documentation, and implementation adapters. It is not automatically trusted because it is listed in this repository.

## Core invariants cannot be weakened

An extension MUST NOT:
- change the meaning of a core MSC contract;
- weaken deny-by-default, explicit DENY precedence, exact policy-version binding, expiry, or fail-closed behavior;
- turn model output, prompts, tool descriptions, peer messages, or caller-supplied principal strings into authority;
- claim that an ALLOW decision proves execution was mediated;
- silently broaden principal, action, target, scope, audience, or expiry;
- silently drop security-relevant context during protocol mapping.

If an extension needs new core fields or new decision semantics, it MUST propose a versioned MASG protocol change rather than silently modifying v1.0.0 envelopes.

## Extension types

- `domain_profile`: maps a domain vocabulary (for example, tool calls, robotics actions, data access, or financial operations) to core action/target/scope semantics.
- `transport_adapter`: maps HTTP, sockets, queues, MCP, A2A, or native IPC messages to core envelopes.
- `identity_adapter`: derives authenticated principals and credential status from an identity provider.
- `policy_adapter`: maps an external policy engine to MASG decision semantics.
- `enforcement_adapter`: applies decisions at a protected side-effect boundary.
- `evidence_adapter`: exports evidence to a defined storage/checkpoint system.
- `recovery_adapter`: integrates trust-separated recovery and restoration workflows.

An extension can implement more than one role, but its manifest and conformance evidence must state each supported role and limitation.

## Namespacing and layout

Extensions use reverse-domain-style identifiers controlled by their maintainers, for example:

`org.huffmanmainnode.masg.generic-tool-action`

The identifier is a namespace label, not proof of ownership or authenticity. Verify publisher identity and release provenance separately.

Suggested repository layout:

```text
extensions/
  <namespace>/
    <extension-name>/
      <version>/
        manifest.json
        README.md
        schemas/
        vectors/
        adapters/
        tests/
        LIMITATIONS.md
```

Extensions may live in independent repositories. MASG does not require a central extension registry, hosted service, package index, or approval authority.

## Compatibility and failure behavior

- An extension MUST declare the MASG protocol versions it supports.
- A consumer MUST reject an extension requiring an unsupported protocol version.
- A consumer MUST fail closed when a required security-critical extension is missing, invalid, untrusted, or unavailable.
- An optional extension may be ignored only when the manifest explicitly marks it non-security-critical and the protected decision does not depend on it.
- Unknown extension-specific fields MUST NOT be injected into v1.0.0 core envelopes. Keep extension metadata out-of-band or map it to existing core fields without loss of security meaning.
- If a mapping cannot preserve identity provenance, action, target, scope, policy version, expiry, or required context, the adapter MUST refuse the operation.
- Extension versions are independent of MASG protocol versions. Breaking extension semantics require a major extension version and migration notes.

## Forks and community changes

Anyone may fork MASG or create an extension. To preserve interoperability:
1. Keep core protocol semantics unchanged when publishing a compatible extension.
2. Use a distinct extension ID for independently maintained semantics.
3. Publish extension-specific schemas, vectors, tests, and limitations.
4. Declare required MSC contracts and protocol versions.
5. Publish a machine-readable manifest and source revision.
6. Never claim upstream conformance if the fork changes normative core semantics.

A fork that changes core semantics is a derivative protocol. It should use a distinct protocol identifier/version and its own conformance suite.

## Assurance and limitations

A valid extension manifest proves only that its metadata matches the schema. It does not authenticate the publisher, validate implementation behavior, prove the adapter secure, or certify a deployment.

The example under `extensions/examples/generic-tool-action/` is documentation and metadata only. It is not an MCP adapter or executable tool broker. There is no central registry, signing authority, automatic trust, or official approval implied by this extension model.
