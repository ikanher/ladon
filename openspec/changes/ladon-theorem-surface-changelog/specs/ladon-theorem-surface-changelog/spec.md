## ADDED Requirements

### Requirement: Theorem Surface Changelog Rows

Ladon SHALL define a future report surface for theorem statement changes with
explicit backend confidence and nonclaims.

#### Scenario: added premise is reported

- **WHEN** a theorem statement gains a premise
- **THEN** Ladon SHALL report an added-premise change with source/backend
  evidence.

#### Scenario: conclusion drift is reported

- **WHEN** the available theorem-surface representation shows conclusion drift
- **THEN** Ladon SHALL report the drift without evaluating mathematical truth.

#### Scenario: proof-only change is separated

- **WHEN** the theorem statement is unchanged but proof text changes
- **THEN** Ladon SHALL report proof-only review context separately.
