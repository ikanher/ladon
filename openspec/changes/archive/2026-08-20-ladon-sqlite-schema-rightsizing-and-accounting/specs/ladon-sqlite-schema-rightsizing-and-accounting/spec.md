## ADDED Requirements

### Requirement: Physical layouts follow measured query keys
High-volume graph tables SHALL use measured query-aligned primary-key order and `WITHOUT ROWID` when benchmark evidence shows lower bytes without slower accepted queries. Forward and reverse traversal MUST each retain a covering access path.

#### Scenario: Lineage edge schema is built
- **WHEN** schema validation inspects the edge relation
- **THEN** uniqueness, both traversal directions, foreign keys, and measured byte reduction are preserved without duplicate forward B-trees

### Requirement: Redundant indexes are rejected
Schema validation SHALL identify indexes whose useful prefix is already provided by a primary key or another accepted index and SHALL require a documented query-plan justification for retaining one.

#### Scenario: Import forward index duplicates its primary key
- **WHEN** the schema index inventory is validated
- **THEN** the redundant index is absent or has an explicit populated-plan and latency justification

### Requirement: Sparse semantic indexes are partial or deferred
Indexes over semantic fields absent from most lexical rows SHALL exclude unavailable/default rows or SHALL be created only for generations that populate the field.

#### Scenario: Lexical generation has no semantic heads
- **WHEN** all declaration heads are empty
- **THEN** the generation does not spend a full-population B-tree on head lookup and exact declaration-name lookup still has its own access path

### Requirement: Storage accounting is first-class evidence
Build, status, and lineage summary SHALL expose deterministic logical row counts and allocated bytes for every application table and index, grouped by base, lineage, ProofIR, FTS, and free-page categories.

#### Scenario: One closure is added
- **WHEN** status is compared before and after refresh
- **THEN** callers can attribute marginal database growth to concrete tables and indexes

### Requirement: Private schema changes rebuild atomically
The optimized schema SHALL use a new private generation identity and SHALL reject old generations with an explicit rebuild instruction; in-place migration is not required.

#### Scenario: Existing schema-v4 database is opened
- **WHEN** its generation does not match the optimized schema
- **THEN** read commands report incompatible schema and do not partially mutate it
