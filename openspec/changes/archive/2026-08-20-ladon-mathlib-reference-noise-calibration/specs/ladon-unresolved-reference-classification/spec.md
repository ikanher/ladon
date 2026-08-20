## ADDED Requirements

### Requirement: Mathlib Reference Noise Calibration

Ladon SHALL keep common mathlib infrastructure and local one-letter theorem
variables out of actionable unresolved-reference findings.

#### Scenario: mathlib roots are external candidates

- GIVEN an unresolved reference candidate starts with `ENNReal` or
  `ProbabilityTheory`
- WHEN Ladon classifies unresolved declaration-reference candidates
- THEN the candidate SHALL be classified as `external_candidate`.

#### Scenario: single uppercase theorem variables are local candidates

- GIVEN an unresolved reference candidate is a single uppercase identifier such
  as `X`, `C`, or `Δ`
- WHEN Ladon classifies unresolved declaration-reference candidates
- THEN the candidate SHALL be classified as `local_type_parameter_candidate`.

#### Scenario: theorem-like names remain actionable

- GIVEN an unresolved reference candidate is a multi-character theorem-like name
  such as `MissingTheorem`
- WHEN Ladon classifies unresolved declaration-reference candidates
- THEN the candidate SHALL remain `actionable_unknown`.
