## ADDED Requirements

### Requirement: Final-name conditional signature warning
The system SHALL emit `ladon.theorem.final_name_conditional_statement` as a
warning-only diagnostic when a final-sounding theorem name still exposes
high-risk conditional or imported evidence premises in its statement.

#### Scenario: Production theorem exposes certificate premise
- **WHEN** a declaration name contains a final, production, maintained, closed, theorem, or eventDP marker and its signature contains `Certificate`
- **THEN** the heuristic emits `ladon.theorem.final_name_conditional_statement` at warning level

#### Scenario: Closed theorem exposes imported row premise
- **WHEN** a declaration name suggests closure and its signature contains `imported` or generic row evidence
- **THEN** the heuristic emits `ladon.theorem.final_name_conditional_statement` at warning level

### Requirement: High-risk premise token set
The heuristic SHALL include a baseline high-risk token set for conditional proof
routes and SHALL keep the token list configurable in future extensions.

#### Scenario: Count-mass evidence premise appears
- **WHEN** a final-sounding theorem signature contains `hcountMassEvidence`
- **THEN** the heuristic emits a warning that routes reviewers to inspect whether the claim is conditional

#### Scenario: CDF evidence premise appears
- **WHEN** a final-sounding theorem signature contains `hForwardCDF` or `hReverseCDF`
- **THEN** the heuristic emits a warning that routes reviewers to inspect imported numeric evidence

### Requirement: Heuristic non-authority
The signature heuristic SHALL NOT emit proof-authority mismatch diagnostics by
itself.

#### Scenario: Conditional signature warning is emitted
- **WHEN** `ladon.theorem.final_name_conditional_statement` is emitted
- **THEN** the diagnostic states that it is a review hint and not proof that the theorem, witness, or claim is invalid

#### Scenario: Route metadata honestly labels conditional evidence
- **WHEN** explicit route metadata already labels the claim as conditional on imported evidence
- **THEN** the heuristic output is suppressed or lowered so the honest route label is not treated as an overclaim
