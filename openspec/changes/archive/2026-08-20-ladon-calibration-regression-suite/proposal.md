# Ladon Calibration Regression Suite

## Why

The pre-registered Quux and matrix-factorization runs produced coherent
signals. We should turn those observations into durable regression checks so
future Ladon changes preserve the useful signal surface while avoiding brittle
full-report snapshots.

## What

- Add predicate-based golden regression checks over Ladon JSON reports.
- Improve root-scope classification so narrow theorem owners are not confused
  with suspicious root selection.
- Add evidence profiles so review packets and witness bundles have different
  expected completeness bars.
- Add a wider root matrix over Quux and matrix-factorization owners.
- Reassess proof-region/atlas overlay after the calibration suite is stable.

## Non-Goals

- No exact JSON golden snapshots.
- No claim that calibration predicates prove repo correctness.
- No CI dependency on sibling repositories unless explicitly invoked.
- No graph clustering until the predicate/regression base is stable.
