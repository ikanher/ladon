## ADDED Requirements

### Requirement: Canonical artifacts remain authoritative
SQLite SHALL be a disposable projection of validated canonical v3 artifacts and SHALL NOT become the canonical interchange representation.

#### Scenario: Database is deleted
- **WHEN** the project-local v3 database is removed
- **THEN** it can be deterministically rebuilt from canonical artifacts without semantic loss

### Requirement: Normalized typed projection
The schema SHALL separately project artifacts, environments, subjects, claims, steps, premises, conclusions, substitutions, observations, check results, surfaces, attachments, coverage, omissions, and extensions.

#### Scenario: Step has three premises
- **WHEN** one v3 step has three ordered premise references
- **THEN** three ordered premise rows link to the same step without encoding the list as an opaque semantic JSON field

### Requirement: Row provenance
Every projected semantic row SHALL retain its source content artifact identity and local JSON pointer or equivalent canonical location.

#### Scenario: Invalid query evidence is reviewed
- **WHEN** a dossier exposes one observation
- **THEN** the receiver can navigate from the row to its canonical artifact and payload location

### Requirement: Query-aligned access paths
Every production SQL family SHALL have a registered populated plan predicate, deterministic ordering, finite cardinality, and indexed foreign-key child paths.

#### Scenario: Complete-slice query
- **WHEN** a populated skewed fixture requests a bounded step slice
- **THEN** query-plan evidence uses step/premise/conclusion keys rather than scanning all derivations

### Requirement: Storage and publication accounting
Build and incremental publication SHALL report logical rows, allocated bytes, per-object marginal bytes, statistics refresh, integrity, foreign keys, and access-path gates before atomic commit.

#### Scenario: Artifact exceeds complete database budget
- **WHEN** projection would exceed the configured complete-database ceiling
- **THEN** publication rolls back and preserves the prior active generation

### Requirement: Extension isolation
Unknown namespaced extensions SHALL be retained as bounded canonical blobs and SHALL NOT affect core indexes or semantic decisions.

#### Scenario: Unsupported extension is large
- **WHEN** an extension exceeds its configured bound
- **THEN** a digest sentinel and omission are stored without indexing extension content
