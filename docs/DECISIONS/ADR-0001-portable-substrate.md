# ADR-0001: Portable Safety Substrate
- Status: Accepted
- Date: 2026-11-09
- Owner: MrCakes931

## Context
Agent systems differ in models, orchestration, memory, protocols, and infrastructure. A centralized service creates another dependency and control point.

## Decision
MASG is a portable contract, verification, and enforcement-integration layer. It does not host agents or require a central service. Adopters retain their models, data, and operations.

## Consequences
Core verification should work offline; integrations remain optional; enforcement belongs at real side-effect boundaries; claims must state assumptions and evidence.
