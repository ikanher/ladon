## Why

The clean pipeline currently records `lean_extraction` as skipped. Ladon needs a
real Lean-native extraction boundary so future declaration graph, proof graph,
and witness checks can use parser-helper output without reintroducing the old
monolith.

## What Changes

- Add an extraction backend option with `text` as the default and `lean` as an
  explicit backend.
- Normalize the bundled Lean parser-helper JSON into the existing `LeanModule`
  IR.
- Record backend-specific pipeline timings and counters.
- Keep declaration-level facts out of scope except for preserving declaration
  names in `LeanModule.declarations`.
- Add tests for parser-output normalization and backend selection without
  requiring a large external Lean repository.

## Capabilities

### New Capabilities

- `ladon-lean-extraction`: Defines the clean Lean-native extraction boundary,
  backend selection behavior, parser-helper normalization, and support limits.

### Modified Capabilities

- `ladon-pipeline`: `lean_extraction` becomes a real timed phase when the Lean
  backend is selected and remains explicitly skipped for text extraction.

## Impact

- Affected code: `src/ladon/extraction.py`, `src/ladon/pipeline.py`,
  `src/ladon/cli.py`, tests.
- Affected CLI: new `--extraction-backend {text,lean}` option.
- Affected reports: pipeline timing counters identify selected extraction
  backend and extracted module counts.
