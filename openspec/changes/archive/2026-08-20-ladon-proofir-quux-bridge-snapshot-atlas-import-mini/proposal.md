## Why

Quux can emit a downstream `ladon_proofir_bridge_snapshot` that already contains
joined bridge rows and diagnostics. Ladon's atlas workflow should be able to
summarize that optional evidence without treating snapshots as the canonical
ProofIR input or as proof truth.

## What Changes

- Normalize `ladon_proofir_bridge_snapshot` rows into atlas workflow bridge
  report summaries when supplied.
- Map snapshot diagnostics to the existing `ruleId`/`level` shape used by atlas
  workflow.
- Preserve source report root identity from snapshot metadata.
- Add tests that snapshot statuses remain quoted context only.

## Capabilities

### New Capabilities

- `ladon-proofir-quux-bridge-snapshot-atlas-import`: Lets atlas workflow consume
  optional Quux/Ladon bridge snapshots as already-rendered evidence summaries.

### Modified Capabilities

None.

## Impact

- Affected code: `src/ladon/atlas_workflow.py` and tests.
- Affected behavior: optional bridge evidence inputs become more tolerant of
  Quux snapshot shape.
