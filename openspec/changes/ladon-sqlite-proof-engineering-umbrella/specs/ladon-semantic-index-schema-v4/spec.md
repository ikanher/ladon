## ADDED Requirements

### Requirement: Semantic schema stores complete indexed evidence
Schema v4 SHALL store normalized declaration metadata, every Lean-supplied leading binder and direct dependency, declaration shapes, structures, fields, external symbol frontiers, and per-module semantic coverage whenever extraction is complete.

#### Scenario: Complete module is inserted
- **WHEN** a validated complete module artifact is populated
- **THEN** terminal counts agree with stored declarations, binders, dependencies, structures, and fields and the module is eligible for completeness claims

### Requirement: Constraints protect semantic relations
The schema MUST enforce primary keys, uniqueness, enumerated checks, non-null status/authority fields, and foreign keys with deliberate delete behavior for all semantic relations.

#### Scenario: Invalid dependency is inserted
- **WHEN** a dependency references a missing source declaration or symbol
- **THEN** insertion fails with foreign-key enforcement enabled

### Requirement: Required access paths are verified
The schema SHALL include exact folded-name, FTS, shape/head, source-dependency, reverse-consumer, structure-field, and module-state indexes, with query-plan tests for public access paths.

#### Scenario: Reverse consumers are planned
- **WHEN** the canonical reverse-consumer query is explained on a populated fixture
- **THEN** the plan uses the target-symbol covering index rather than scanning all dependencies

### Requirement: Schema generations are disposable and explicit
An incompatible earlier proof-search database SHALL be reported as rebuild-required and MUST NOT be migrated in place during query execution.

#### Scenario: Version-three database is opened
- **WHEN** schema-v4 code inspects the prior generation
- **THEN** status provides a deterministic rebuild instruction without executing partial v4 SQL
