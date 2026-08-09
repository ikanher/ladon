## ADDED Requirements

### Requirement: Base-build and complete-database budgets are distinct
Build and status results SHALL report the base-build ceiling, complete-database ceiling, current logical and allocated bytes, percentage of each applicable ceiling, and the policy source. Lineage refresh MUST obey the complete-database ceiling.

#### Scenario: Base index fits but lineage would exceed the complete ceiling
- **WHEN** estimated or transactional lineage growth crosses the configured complete-database limit
- **THEN** publication fails explicitly and the previously active closure and database remain usable

### Requirement: Lineage publication is measured and transactional
Refresh SHALL measure pre-publication bytes, estimated rows, post-insert bytes, marginal bytes by affected table/index where available, integrity and foreign-key results, and commit only after every budget and validation gate passes.

#### Scenario: Validation fails after rows are inserted
- **WHEN** size, integrity, foreign-key, or statistics validation fails inside publication
- **THEN** the transaction rolls back without deactivating or deleting the prior closure

### Requirement: Planner statistics follow mutable evidence
Successful lineage publication or replacement SHALL refresh statistics for affected lineage tables before commit and record statistics identity or timestamp in status evidence.

#### Scenario: First closure is added after base optimization
- **WHEN** lineage tables transition from empty to populated
- **THEN** `sqlite_stat1` contains current lineage entries and populated plan gates pass before success is reported

### Requirement: Refresh emits progress and exactly one terminal result
The CLI SHALL emit bounded phase progress for planning, Lean extraction, persistence, optimization, projection, and output, and SHALL emit exactly one terminal success or failure record distinguishing timeout, resource termination, budget rejection, persistence failure, rendering failure, and success.

#### Scenario: Persistence succeeds but rendering fails
- **WHEN** the closure commits but the requested presentation cannot be produced
- **THEN** the terminal failure identifies successful persistence and failed presentation without implying the refresh was wholly absent

### Requirement: Requested output publication is atomic
File output SHALL be written to a sibling temporary file, flushed, atomically replaced, and reported only after replacement; failed rendering MUST NOT leave a partial requested file.

#### Scenario: Process stops during rendering
- **WHEN** output generation is interrupted before replacement
- **THEN** the prior output remains unchanged or no output exists
