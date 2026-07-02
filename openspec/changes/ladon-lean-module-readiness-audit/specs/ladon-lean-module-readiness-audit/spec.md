## ADDED Requirements

### Requirement: Module readiness rows
The system SHALL emit module-readiness rows for public facade pressure,
implementation public pressure, generated aggregation, namespace/module drift,
and optional module-system witness evidence.

#### Scenario: Readiness rows are reported
- **WHEN** module DAG or declaration evidence contains module-boundary pressure
- **THEN** Ladon reports module-readiness rows with source evidence and nonclaim wording

### Requirement: Module-system witness metadata
The system SHALL preserve backend, tool version, command, content hash,
visibility, status, and confidence metadata from module-system witness rows.

#### Scenario: Weak witness metadata
- **WHEN** a witness row lacks backend, version, command, or content hash metadata
- **THEN** Ladon labels the row weak and does not use it as strong authority
