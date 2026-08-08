## ADDED Requirements

### Requirement: Constructor fields are instantiated by Lean
`proof-search constructor coverage` SHALL inspect the requested structure and constructor in the selected module environment and return exactly one ordered record per unresolved instantiated field.

#### Scenario: Structure has dependent fields
- **WHEN** a later field type depends on an earlier parameter or field
- **THEN** Lean supplies the correctly instantiated field goal and source projection identity

### Requirement: Field coverage uses verified candidate evidence
The engine SHALL batch SQL shortlists and Lean checks across fields and classify each as supplied in scope, supplied with residual premises, supplied under stronger hypotheses, restricted boundary, unmatched, or unavailable.

#### Scenario: Field candidate needs a retained-row guard
- **WHEN** its conclusion matches but a row-bound premise remains
- **THEN** the field is classified as restricted or premised with the exact residual and route card

### Requirement: Field classification preserves authority
Quantitative and measure-theoretic adapter labels SHALL name registry authority when configured; heuristic fallback MUST be labelled `heuristic_classification` and MUST NOT drive proof correctness.

#### Scenario: Heuristic recognizes a norm inequality
- **WHEN** no registry rule applies
- **THEN** the row may be labelled quantitative heuristically while remaining separate from Lean applicability evidence

### Requirement: Certificate leakage is explicit
Coverage SHALL test and separately report definitionally equivalent field inputs, direct projection dependencies, and alias/reducible projection dependencies with exact binders or dependency edges and verification state.

#### Scenario: Helper accepts its target certificate
- **WHEN** a helper binder type is definitionally equal to the field it purports to supply
- **THEN** an `equivalent_field_input` finding identifies the binder and Lean verification
