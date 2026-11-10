# Generic Tool Action Profile (Example Only)

This is an example domain mapping, not a working tool adapter.

| External concept | MASG v1.0.0 field | Example |
|---|---|---|
| Authenticated workload | principal | `spiffe://example.org/agent/report-reader` |
| Tool operation | action | `tool.invoke` |
| Stable tool identity | target | `mcp://reports-server/tools/read-weekly` |
| Authorized operation subset | scope | `report.read.summary` |
| Selected policy | policy_version | `report-policy-7` |

## Mapping requirements

- The adapter, not the model or caller, establishes the principal.
- The target must identify the intended tool server and tool without ambiguous aliases.
- Scope must represent the narrow operation and resource boundary. A generic `*` scope is not a safe default.
- The adapter must validate the selected policy version, request expiry, and all relevant provenance before requesting a decision.
- The executor must enforce the result at the actual tool side-effect boundary. A policy ALLOW response alone does not enforce anything.
- If tool identity, scope, or input context cannot be represented without losing security meaning, refuse the call.

The manifest is in `manifest.json`. This example has no executable adapter, no MCP dependency, and no identity authentication.
