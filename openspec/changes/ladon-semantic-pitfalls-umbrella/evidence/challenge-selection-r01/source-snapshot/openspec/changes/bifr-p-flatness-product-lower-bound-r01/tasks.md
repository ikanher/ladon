## 1. Lower-Bound Surface Audit

- [x] 1.1 Inspect `BIFRMultiParticipationSensitivityLowerBound.lean` and list
  the row, uniform-floor, and per-lag lower-bound seams available.
- [x] 1.2 Inspect `BIFRProductObjectiveLowerBoundProgram.lean` and
  `BIFRProductObjectiveHalfSliceLowerWitness.lean` for the shortest product
  endpoint to target.
- [x] 1.3 Decide whether the first theorem is half-slice, fixed-witness, or
  optimizer-uniform.

## 2. Coefficient Profile Target

- [x] 2.1 Choose a row index and packed count/separation regime with scalar
  fit conditions.
- [x] 2.2 Formulate a coefficient floor or per-lag profile theorem for selected
  BIFR factor coefficients.
- [x] 2.3 Decide no new exact finite witness diagnostic is needed for this pass:
  the selected half-slice packed-profile route is already Lean-backed.

## 3. Product Composition

- [x] 3.1 Feed the coefficient profile into the packed sensitivity row seam.
- [x] 3.2 Compose the sensitivity row lower bound with an inverse-side prefix
  lower witness.
- [x] 3.3 State the resulting lower bound with explicit gamma/family scope.

## 4. Validation And Docs

- [x] 4.1 Run focused `lake build` for touched Lean owners.
- [x] 4.2 No checker tests added; no finite artifact was introduced in this pass.
- [x] 4.3 Update lower-bound/tightness docs with closed and open claims.
- [x] 4.4 Run `openspec validate bifr-p-flatness-product-lower-bound-r01 --strict`.
