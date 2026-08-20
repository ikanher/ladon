## Why

Ladon already has proof-surface route auditing. The missing piece is a clear
handoff from project-local Lean verifier scripts into that existing witness
contract, plus reviewer summaries of route-evidence completeness.

## What Changes

- Preserve verifier handoff metadata on proof-surface rows and axiom audits.
- Add route-evidence completeness summaries derived from existing proof-surface
  predicates.
- Document that generation is project-local and Ladon only consumes quoted
  witness metadata.

## Capabilities

### New Capabilities

- `ladon-proof-surface-witness-generation-handoff`: Optional verifier handoff
  metadata and completeness summaries for existing proof-surface route audit.

### Modified Capabilities

None.

## Impact

- Affected code: proof-surface witness normalization, route output, docs, and
  tests.
