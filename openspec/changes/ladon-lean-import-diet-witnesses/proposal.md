## Why

Lean/Lake can provide stronger import-minimization evidence than Ladon's text
DAG. Ladon should consume that evidence as an optional witness and route review
to redundant-import candidates without becoming the import minimizer.

## What Changes

- Add compact import-diet witness ingestion.
- Compare fresh witness rows to observed import sites.
- Report redundant-import candidates and stale witness diagnostics.
- Rank candidates by graph impact and render nonclaim text.

## Capabilities

### New Capabilities

- `ladon-lean-import-diet-witnesses`: Optional Lean/Lake import-diet witness
  ingestion and report comparison.

### Modified Capabilities

None.

## Impact

- Affected code: optional JSON input, pipeline, rendering, import-site evidence,
  docs, and benchmark fixtures.
