## ADDED Requirements

### Requirement: Reproducible baseline evidence
The system SHALL record proof-search correctness, startup, SQL-count, build, query, database-size, and peak-memory baselines with command, repository, toolchain, schema, and host identities.

#### Scenario: Baseline is rerun
- **WHEN** a developer runs the documented baseline harness on a supported checkout
- **THEN** it emits machine-readable measurements and all identities needed to compare a later run on the same host

### Requirement: Known failures remain explicit
The baseline suite SHALL reproduce known mixed-case, refinement, duplicate-traversal, and N+1 defects as identified expected failures rather than normalizing them into passing snapshots.

#### Scenario: Known defect is captured
- **WHEN** the pre-fix implementation exhibits a preregistered defect
- **THEN** the fixture identifies the defect and names the child packet responsible for removing the expected failure

### Requirement: Contract fixtures are semantic
Public result fixtures MUST assert required fields, authority, freshness, bounds, omissions, collection names, and deterministic ordering without coupling to private SQLite layout.

#### Scenario: Private table changes
- **WHEN** a private schema implementation changes without changing the public result
- **THEN** the contract fixture continues to pass
