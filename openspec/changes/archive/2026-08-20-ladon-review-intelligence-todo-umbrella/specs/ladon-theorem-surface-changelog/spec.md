## ADDED Requirements

### Requirement: Theorem Surface Changelog

Ladon SHALL define a future Lean-backed changelog surface for theorem
statements that classifies changes without claiming theorem truth.

#### Scenario: added premise is classified

- **WHEN** a theorem's statement changes by adding a required premise
- **THEN** Ladon SHALL classify the theorem surface change as an added premise
  with source evidence and backend confidence.

#### Scenario: conclusion drift is classified

- **WHEN** a theorem's conclusion is weakened, strengthened, or otherwise
  changed according to the available theorem-surface representation
- **THEN** Ladon SHALL report the statement drift without claiming whether the
  new theorem is mathematically preferable.

#### Scenario: proof-only change is separated

- **WHEN** a theorem type is unchanged but proof text or proof metadata changes
- **THEN** Ladon SHALL separate proof-only review context from theorem-surface
  statement drift.
