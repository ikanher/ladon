## ADDED Requirements

### Requirement: Root Matrix Evidence Pass

Ladon SHALL support evidence-driven calibration runs over maintained root
matrices.

#### Scenario: maintained roots are evaluated

- GIVEN a maintained root matrix
- WHEN the evidence pass runs
- THEN each selected root SHALL produce JSON and text reports.

#### Scenario: reports are summarized

- GIVEN generated root-matrix reports
- WHEN the evidence pass is reviewed
- THEN it SHALL record root-level findings, grouped review regions, and any
  concrete analyzer misses or false positives.

#### Scenario: follow-up work is evidence-bound

- GIVEN the evidence pass finds no repeatable analyzer defect
- WHEN deciding next work
- THEN Ladon SHOULD avoid adding a new smell heuristic solely from speculation.
