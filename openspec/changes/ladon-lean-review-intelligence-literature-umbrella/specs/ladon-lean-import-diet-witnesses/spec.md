## ADDED Requirements

### Requirement: Import diet witness input
The system SHALL accept an optional compact import-diet witness artifact that
quotes Lean-owned or Lake-owned import minimization evidence without requiring
the core analyzer to run import minimization by default.

#### Scenario: witness is supplied
- **WHEN** a valid import-diet witness is supplied with module, original imports, minimized imports, tool name, tool version, command, and confidence fields
- **THEN** Ladon normalizes the witness and includes it in the report as quoted import-diet evidence

#### Scenario: witness is missing
- **WHEN** no import-diet witness is supplied
- **THEN** Ladon skips Lean-owned import minimization evidence and continues to report text-backed import DAG pressure

### Requirement: Import DAG comparison
The system SHALL compare import-diet witness rows against Ladon's observed
direct imports and report agreement, stale witness rows, and candidate redundant
imports.

#### Scenario: redundant import candidate
- **WHEN** a witness omits an import that Ladon observes in source and the witness is fresh for the same module/source hash
- **THEN** Ladon reports the observed import as a redundant-import candidate with source path, line, import text, witness command, and confidence

#### Scenario: stale import witness
- **WHEN** witness source hash or module inventory metadata does not match Ladon's current source evidence
- **THEN** Ladon emits a stale-witness diagnostic and does not use the witness to classify imports as redundant

### Requirement: Import-diet nonclaims
The system SHALL state that import-diet rows are build/refactor evidence only
and do not establish theorem truth, proof dependency, or import removability
without replay.

#### Scenario: report renders import-diet finding
- **WHEN** an import-diet finding appears in JSON, text, atlas, or reviewer-card output
- **THEN** the output includes nonclaim text saying Ladon is quoting import-minimization evidence and not proving that an import can be safely removed without the named Lean/Lake command

### Requirement: Critical path ranking
The system SHALL rank import-diet candidates by review impact using available
module DAG evidence such as fan-in, fan-out, root closure, generated status, and
facade role.

#### Scenario: high-impact import candidate
- **WHEN** multiple redundant-import candidates exist and one is on a high fan-in or root-closure path
- **THEN** Ladon ranks that candidate ahead of lower-impact rows and includes the ranking evidence
