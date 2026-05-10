## ADDED Requirements

### Requirement: Predicate-Based Calibration Regressions

Ladon SHALL provide predicate-based regression checks over report JSON.

#### Scenario: predicate pass and fail rows

- GIVEN a report payload and predicate list
- WHEN predicates are evaluated
- THEN Ladon SHALL return structured rows showing which predicates passed and
  failed.

#### Scenario: built-in Quux/MF suites

- GIVEN a reports directory using Ladon's current live-run layout
- WHEN the built-in suite is evaluated
- THEN Ladon SHALL check stable Quux and matrix-factorization signal
  predicates without exact JSON snapshots.

#### Scenario: missing reports are explicit failures

- GIVEN an expected report file is absent
- WHEN the built-in suite is evaluated
- THEN Ladon SHALL report a failed missing-report row rather than crashing.
