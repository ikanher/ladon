## ADDED Requirements

### Requirement: Every selective production query has a populated access-path test
Schema acceptance SHALL inventory each production equality, range, join, anti-join, ordering, recursive edge, and foreign-key child predicate and SHALL run `EXPLAIN QUERY PLAN` against nonempty representative data.

#### Scenario: Required index names exist but a query scans its relation
- **WHEN** populated plan inspection reports an avoidable full scan for a selective operation
- **THEN** schema acceptance fails even though the declared index-name inventory passes

### Requirement: Exact declaration and attachment lookup are directly indexed
Exact declaration name, candidate name, selected attachment by declaration, surface by declaration, and related artifact lookups SHALL use access paths whose leading columns match their predicates.

#### Scenario: Theorem dossier resolves a declaration
- **WHEN** a theorem has one selected ProofIR attachment among a large declaration population
- **THEN** declaration and attachment resolution use direct searches rather than skip-scans or full scans

### Requirement: ProofIR dossier graph and diagnostic lookups are indexed
Diagnostics by artifact, DAG edges by source, target, and obligation, replay relations, claim joins, and node identities SHALL have measured access paths matching dossier query shapes.

#### Scenario: Dossier asks for one obligation
- **WHEN** the obligation occurs in one DAG among many
- **THEN** the query searches by DAG and obligation identity without scanning all DAG edges

### Requirement: Negative-evidence triage uses compact selective paths
Sparse stale, failed, foreign, unmatched, malformed, unsupported, and disconnected conditions SHALL use partial or leading-predicate indexes when measurements show a selective population.

#### Scenario: One stale attachment exists among many fresh attachments
- **WHEN** repository triage requests stale evidence with a finite limit
- **THEN** the plan searches the stale subset and returns deterministically without scanning every attachment

### Requirement: Foreign-key child paths are audited
Every foreign-key child relation that participates in replacement, cascade, or attachment selection SHALL have a primary-key prefix or explicit index suitable for the parent-side operation.

#### Scenario: ProofIR generation is replaced
- **WHEN** old generation rows are removed transactionally
- **THEN** foreign-key enforcement does not require unindexed scans of child relations
