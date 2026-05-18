## ADDED Requirements

### Requirement: Lean Reference Noise Calibration

Ladon SHALL keep known Lean infrastructure and common local type-parameter
spellings out of promoted actionable unresolved-reference findings.

#### Scenario: Lean infrastructure roots are external candidates

- GIVEN an unresolved reference candidate starts with `WellFounded`
- WHEN Ladon classifies unresolved declaration-reference candidates
- THEN the candidate SHALL be classified as `external_candidate`.

#### Scenario: common local type parameters are not actionable

- GIVEN an unresolved reference candidate is a known generic type-parameter
  spelling such as `Edge`
- WHEN Ladon classifies unresolved declaration-reference candidates
- THEN the candidate SHALL be classified as `local_type_parameter_candidate`.

#### Scenario: raw unresolved rows are preserved

- GIVEN local type-parameter candidates appear in unresolved rows
- WHEN Ladon emits declaration graph summaries
- THEN raw unresolved rows SHALL still include those candidates and their
  classification.

#### Scenario: actionable rows exclude calibrated noise

- GIVEN unresolved candidates include local type-parameter candidates and Lean
  external infrastructure
- WHEN Ladon emits actionable unresolved rows
- THEN those calibrated candidates SHALL NOT appear in
  `top_actionable_unresolved_references`.
