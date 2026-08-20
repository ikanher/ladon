## Why

Current calibration relies partly on fixed thresholds and stale external
repository cardinalities. Ladon needs repeatable measurements of signal
correctness, extraction coverage, resource cost, and report stability to decide
when alpha behavior is promotable.

## What Changes

- Build portable positive, negative, and boundary fixtures for promoted module,
  declaration, proof-surface, and CLI signals.
- Measure precision/false-positive rate for heuristic findings, recall for
  known missing imports, and coverage for declaration/dependency extraction.
- Measure cold/warm wall time, peak RSS, cache behavior, timeout cleanup, report
  size, and deterministic output.
- Version benchmark manifests and thresholds with the product/report version;
  do not encode a moving repository's exact module count as correctness.
- Run portable correctness and bounded performance checks in CI, with clearly
  separated optional Quux, matrix-factorization, and mathlib smokes.
- Produce machine-readable results and a compact developer summary without
  introducing a second product-analysis path.

## Capabilities

### New Capabilities

- `ladon-signal-benchmark-harness`: Portable correctness, coverage,
  performance, memory, cache, and stability measurements for promoted Ladon
  behavior.

### Modified Capabilities

None.

## Impact

- Affected code and data: benchmark fixtures, oracle helpers, performance
  runner, CI jobs, calibration predicates, baseline manifests, and docs.
- Affected promotion workflow: new or changed findings require measured
  positive/negative behavior before becoming default output.
- External repositories remain optional evidence and cannot make required CI
  depend on hard-coded local paths.
