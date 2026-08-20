## ADDED Requirements

### Requirement: Generated Artifact Attribution

Ladon SHALL distinguish generated artifact pressure from handwritten source
pressure and attribute generated duplicate imports when evidence is available.

#### Scenario: duplicate imports are grouped by generated family

- **WHEN** duplicate imports appear in generated modules
- **THEN** Ladon SHALL summarize duplicate module count by generator family and
  target.

#### Scenario: handwritten tables exclude generated rows

- **WHEN** handwritten fan-in/fan-out or large-file tables are produced
- **THEN** generated modules SHALL not appear in those handwritten-focused
  tables.

#### Scenario: cleanup hint is non-authoritative

- **WHEN** Ladon reports a generated duplicate import
- **THEN** the suggested action SHALL be a review hint and SHALL NOT claim the
  generator is proven defective.
