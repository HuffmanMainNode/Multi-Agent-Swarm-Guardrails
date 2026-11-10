# MASG Extensions

This directory contains extension packaging guidance and examples. It is not a central registry or an automatic trust list.

Read [docs/EXTENSION_MODEL.md](../docs/EXTENSION_MODEL.md) before creating an extension.

## Example

`examples/generic-tool-action/` demonstrates a namespaced domain-profile manifest and mapping conventions. It is metadata and documentation only, not a working transport or tool adapter.

Independent extensions may live in their own repositories. Keep core protocol semantics unchanged for compatibility; extensions cannot weaken core security invariants.