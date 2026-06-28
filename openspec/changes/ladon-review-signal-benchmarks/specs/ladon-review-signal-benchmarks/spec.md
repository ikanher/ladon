## ADDED Requirements

### Requirement: Portable Review Signal Benchmarks

Ladon SHALL maintain portable fixtures and predicate oracles for promoted
review signals.

#### Scenario: positive fixture asserts signal

- **WHEN** a signal is promoted
- **THEN** a portable fixture SHALL assert the expected finding or report row.

#### Scenario: negative fixture asserts boundary

- **WHEN** a legitimate pattern resembles a smell
- **THEN** a portable fixture SHALL assert that Ladon does not overflag it.

#### Scenario: private smoke is optional

- **WHEN** live Matrix-Factorization or Quux smoke evidence is recorded
- **THEN** required CI SHALL remain reproducible without those repositories.
