## ADDED Requirements

### Requirement: Review Signal Benchmark Fixtures

Ladon SHALL maintain portable benchmark fixtures and oracle checks for promoted
review signals before those signals are treated as reliable reviewer findings.

#### Scenario: positive fixture covers promoted signal

- **WHEN** a new architecture, source-pattern, claim-authority, generated, or
  facade signal is promoted
- **THEN** a portable fixture SHALL demonstrate the expected positive finding.

#### Scenario: negative fixture covers false-positive boundary

- **WHEN** a promoted signal has a known legitimate pattern
- **THEN** a portable negative fixture SHALL show that Ladon does not overflag
  the legitimate case.

#### Scenario: private smoke stays optional

- **WHEN** Matrix-Factorization or Quux smoke evidence is recorded
- **THEN** the core CI oracle SHALL remain reproducible without requiring those
  sibling repositories.
