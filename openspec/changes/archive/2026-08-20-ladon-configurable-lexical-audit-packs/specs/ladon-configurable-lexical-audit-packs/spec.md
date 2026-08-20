## ADDED Requirements

### Requirement: Source Pattern Policy Packs

Ladon SHALL support reusable source-pattern policy pack examples and tests
without hard-coding project vocabulary.

#### Scenario: pack match is source-located

- **WHEN** a policy-pack pattern matches source text
- **THEN** Ladon SHALL report pattern id, kind, severity, source path, line,
  module, generated status, and sample text.

#### Scenario: capped report preserves total count

- **WHEN** a pattern exceeds its report cap
- **THEN** Ladon SHALL report both total and reported match counts.

#### Scenario: zero-match pack reports coverage

- **WHEN** no pattern matches
- **THEN** Ladon SHALL report zero counts per pattern.
