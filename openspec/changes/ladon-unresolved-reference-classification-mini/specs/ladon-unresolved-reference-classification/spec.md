## ADDED Requirements

### Requirement: Unresolved Reference Classification

Ladon SHALL classify unresolved declaration-reference candidates without hiding
the raw unresolved count.

#### Scenario: raw unresolved rows include classification

- GIVEN declaration graph analysis sees unresolved candidates
- WHEN it emits `top_unresolved_references`
- THEN each row SHALL include a deterministic `classification`.

#### Scenario: actionable rows exclude known noise classes

- GIVEN unresolved candidates include parser noise, local/field candidates,
  external candidates, and actionable unknowns
- WHEN declaration graph analysis emits actionable unresolved rows
- THEN `top_actionable_unresolved_references` SHALL include only actionable
  unknown rows.

#### Scenario: findings use actionable unresolved rows

- GIVEN both noisy and actionable unresolved candidates exist
- WHEN findings are summarized
- THEN unresolved-reference hotspot findings SHALL be based on actionable rows.

#### Scenario: text report renders classifications

- GIVEN unresolved rows include classifications
- WHEN text rendering runs
- THEN the text report SHALL show classification labels beside unresolved
  candidates.
