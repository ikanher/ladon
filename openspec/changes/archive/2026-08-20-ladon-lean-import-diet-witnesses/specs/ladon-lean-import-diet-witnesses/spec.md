## ADDED Requirements

### Requirement: Import-diet witness comparison
The system SHALL compare fresh import-diet witness rows against observed import
sites and report redundant-import candidates.

#### Scenario: Redundant import candidate
- **WHEN** a fresh witness omits an observed source import from its minimized import set
- **THEN** Ladon reports the import with source path, line, import text, command, and confidence

### Requirement: Stale witness safety
The system SHALL avoid classifying imports as redundant from stale or malformed
import-diet witnesses.

#### Scenario: Missing module witness row
- **WHEN** a witness row references a module absent from the current module DAG
- **THEN** Ladon emits a stale witness row and does not emit a redundant-import candidate for that row
