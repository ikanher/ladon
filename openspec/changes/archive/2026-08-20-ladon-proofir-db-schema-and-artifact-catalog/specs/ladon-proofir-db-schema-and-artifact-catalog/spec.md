## ADDED Requirements

### Requirement: ProofIR evidence uses the project-local index lifecycle
The system SHALL store ProofIR catalog evidence in the existing project-local
proof-search SQLite database and SHALL use the same resolved repository,
`--index` override, build lock, unpublished-generation validation, atomic
replacement, and size limit as the base index.

#### Scenario: Default database location
- **WHEN** a project with configured ProofIR inputs builds its default index
- **THEN** catalog rows are published in `<repo>/.ladon/index/proof-search.sqlite` and no second database is created

#### Scenario: Failed unpublished generation
- **WHEN** ProofIR catalog ingestion violates a cap, constraint, or integrity check
- **THEN** the previous canonical database remains byte-for-byte available and the temporary generation is not published

### Requirement: Configured artifacts have deterministic identities
The system SHALL catalog only repository-owned explicitly configured artifact
files or bounded globs and SHALL identify every artifact by generation,
repository-relative path, full content hash, artifact kind, and schema version.

#### Scenario: Idempotent identical input
- **WHEN** the same configured artifact bytes are encountered twice in one generation
- **THEN** one artifact identity is stored and no semantic or relationship row can be duplicated

#### Scenario: Path escapes repository
- **WHEN** a configured artifact path resolves outside the repository
- **THEN** ingestion is rejected before publication with a configuration diagnostic

#### Scenario: Artifact bytes change
- **WHEN** a configured artifact changes without changing its relative path
- **THEN** the generation and artifact content identities change and prior freshness is not reused

### Requirement: Catalog support and semantic support are distinct
The system SHALL record whether each artifact is normalized, catalog-only,
malformed, stale, or unavailable and SHALL prevent unsupported or malformed
artifacts from creating semantic evidence rows.

#### Scenario: Unsupported artifact kind
- **WHEN** a valid JSON artifact has an unrecognized `artifactKind`
- **THEN** it receives a catalog row and unsupported coverage diagnostic but creates no claims, surfaces, graph nodes, graph edges, or attachments

#### Scenario: Malformed JSON
- **WHEN** a configured file is not valid JSON or is not a supported top-level object
- **THEN** the generation reports malformed input under the configured failure policy and does not interpret partial semantic rows

#### Scenario: No configured inputs
- **WHEN** a project configures no ProofIR artifact inputs
- **THEN** ProofIR coverage is unavailable/not-configured rather than a confirmed empty ProofIR population

### Requirement: Catalog schema is constrained and indexed
The system SHALL define primary keys, foreign keys, check constraints, and named
lookup indexes for artifact generations, artifacts, artifact relationships, and
diagnostics, and SHALL validate their exact definitions before publication.

#### Scenario: Orphan relationship
- **WHEN** an artifact relationship references a missing source or target artifact
- **THEN** foreign-key validation rejects the unpublished generation

#### Scenario: Required lookup paths
- **WHEN** schema validation inspects active-generation, kind/schema, path/hash, relationship-source, relationship-target, and diagnostic-reason indexes
- **THEN** every required index exists with the prescribed ordered columns

#### Scenario: Query plan regression
- **WHEN** an exact artifact path/hash or relationship lookup is explained
- **THEN** SQLite uses the corresponding named index rather than a full artifact-table scan

### Requirement: Resource limits are explicit
The system SHALL enforce configured file-count, per-artifact byte, total artifact
byte, diagnostic, and stored-metadata limits and SHALL report which limit stopped
the generation.

#### Scenario: Total byte cap crossed
- **WHEN** configured artifacts exceed the total ProofIR input byte cap
- **THEN** ingestion stops deterministically, reports the observed and allowed bytes, and preserves the prior generation

#### Scenario: Bounded metadata
- **WHEN** a supported top-level metadata field exceeds its stored-text cap
- **THEN** the stored value is bounded and a truncation diagnostic points to the source artifact

### Requirement: Rebuilds reproduce configured evidence
The system SHALL include ProofIR configuration and artifact fingerprints in the
captured generation recipe so a base-index rebuild cannot silently discard
configured ProofIR catalog evidence.

#### Scenario: Two unchanged rebuilds
- **WHEN** an index with configured ProofIR artifacts is built twice without input changes
- **THEN** both published generations expose the same artifact identities, relationships, counts, and coverage

#### Scenario: Configuration removed
- **WHEN** ProofIR inputs are removed from configuration and the index is rebuilt
- **THEN** the new generation reports not-configured coverage rather than retaining stale catalog rows
