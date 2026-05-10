# Design

## Child Order

1. `golden-predicate-regressions`
   - Durable predicates over generated reports.
   - Examples: `Quux.Basic` top fan-in, BIFR proof-family candidates, r37 packet
     evidence partial.

2. `root-scope-classification`
   - Distinguish narrow theorem owners from potentially mistaken root choices.
   - Preserve root-scope pressure, but classify why it appeared.

3. `evidence-profiles`
   - Separate review-packet and witness-bundle evidence expectations.
   - Avoid implying a review packet failed a witness-bundle gate.

4. `wider-root-matrix`
   - Add a maintained local run matrix over Quux and matrix-factorization roots.
   - Store commands and predicate expectations, not massive report fixtures.

5. `proof-region-atlas-overlay`
   - Group proof-family and import-closure signals into review regions after
     calibration predicates are stable.

## Calibration Boundary

Regression predicates are quality gates for Ladon behavior. They do not assert
that the target repositories are architecturally correct or incorrect.
