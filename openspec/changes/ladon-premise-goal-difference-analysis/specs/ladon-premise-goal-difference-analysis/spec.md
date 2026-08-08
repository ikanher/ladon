## ADDED Requirements

### Requirement: Candidate application differences are complete
`proof-search explain` SHALL return the elaborated goal and candidate type, attempted conclusion passes, substitutions, locally discharged binders, residual proof premises, unresolved instances/terms, and whether the conclusion matched.

#### Scenario: Conclusion matches with one premise
- **WHEN** Lean applies a candidate conclusion but one proof binder remains
- **THEN** the result is `applicable_with_residual_premises` and contains the exact remaining premise

### Requirement: Mismatch classifications are conservative
Failed conclusion matches SHALL include bounded structural differences and MAY add generic or registry classifications only with rule identity and authority; otherwise they MUST remain unclassified.

#### Scenario: Difference has no registered meaning
- **WHEN** the structural expressions differ and no rule applies
- **THEN** the result uses `unclassified_expression_difference` rather than inventing a semantic explanation

### Requirement: Premise suggestions are Lean verified
For every residual proof premise, the system SHALL derive bounded SQLite shortlists and batch all premise/candidate checks into at most one additional Lean request in P0.

#### Scenario: Existing lemma discharges a premise
- **WHEN** a shortlisted declaration is verified against a residual premise
- **THEN** it appears as a one-level suggestion with substitutions, residuals, ranking, and authority

### Requirement: Route cards are reusable evidence
Every explanation SHALL emit `ladon-proof-route-card-v1` containing exact goal/context/generation/policy identities, candidate, application evidence, suggestions, source anchors, bounds, omissions, accepted/rejected reason, and replay status.

#### Scenario: Candidate is rejected
- **WHEN** the conclusion cannot match under configured passes
- **THEN** a rejected route card preserves the attempted route and exact reason with `not-replayed` status
