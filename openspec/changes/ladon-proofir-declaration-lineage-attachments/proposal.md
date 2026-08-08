## Why

The principal benefit of database-backed ProofIR is joining external evidence
to Ladon's declaration and theorem-lineage surfaces. That join must tolerate
real duplicate declaration names and must never infer theorem evidence from
module names, descriptions, or nearby artifacts.

## What Changes

- Resolve surfaces to declaration IDs using exact source hash/path/name first,
  then conservative source-range evidence with explicit confidence.
- Represent ambiguous, stale, unmatched, and module-context-only candidates as
  diagnostics rather than selecting the first declaration row.
- Join exact attachments to active theorem-lineage nodes while preserving
  separate edge kinds and authorities.
- Add theorem-to-ProofIR and ProofIR-to-declaration/lineage query projections
  with explicit unsupported, stale, and unavailable states.
- Make the Quux CDC theorem a negative oracle: nearby CDC artifacts are visible
  as context but are not attached without an explicit theorem identity.

## Capabilities

### New Capabilities

- `ladon-proofir-declaration-lineage-attachments`: Source-first declaration
  attachment and non-promoting theorem-lineage overlays over stored ProofIR
  evidence.

### Modified Capabilities

None.

## Impact

- Extends declaration lookup, ProofIR joins, lineage projections, diagnostics,
  indexes, and query result contracts.
- Adds duplicate-name fixtures based on the observed Matrix-Factorization
  declaration population and negative CDC attachment tests.
