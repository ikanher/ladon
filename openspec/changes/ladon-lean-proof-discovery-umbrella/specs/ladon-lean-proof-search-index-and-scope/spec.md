## ADDED Requirements

### Requirement: Versioned Lean-aware local index
Ladon SHALL materialize a versioned persistent local query index containing fully
qualified names, kinds, elaborated signatures and binders, owner modules, source
ranges, direct Lean-observed dependencies, aliases/exports, and structure
relationships. The storage format SHALL remain an internal implementation detail.

#### Scenario: Indexed declaration row
- **WHEN** an elaborated project declaration is indexed
- **THEN** its row records the toolchain/helper/schema generation, module/package ownership, source evidence, type data, binder data, and available dependency and structure metadata

#### Scenario: Lexical-only row
- **WHEN** elaborated evidence is unavailable but lexical inventory is permitted
- **THEN** the row is labeled lexical fallback and cannot satisfy a Lean-confirmed query stage

#### Scenario: Repository-local default
- **WHEN** a caller explicitly builds an index without supplying an index path
- **THEN** Ladon uses `<repo>/.ladon/index/proof-search.sqlite`, identifies the subtree as disposable generated state, and does not edit repository ignore files

#### Scenario: Explicit external location
- **WHEN** a caller supplies `--index PATH` for a read-only checkout or CI job
- **THEN** Ladon uses that location while retaining the target repository identity and the same freshness contract

#### Scenario: Indexed graph access paths
- **WHEN** the alpha SQLite backend creates a generation
- **THEN** it creates tested lookup indexes for names, ownership, source paths, semantic tokens, structure membership, and both directions of dependency edges without making SQL graph traversal authoritative for whole-graph analysis

### Requirement: Constrained and validated index generations
Every published generation MUST satisfy declared relational integrity and finite
storage, row, and per-value limits. A failed replacement MUST preserve the prior
complete generation.

#### Scenario: Required relational constraints
- **WHEN** the alpha SQLite backend finishes an unpublished generation
- **THEN** all required foreign keys and lookup surfaces are present and SQLite integrity and foreign-key checks pass before publication

#### Scenario: External names remain representable
- **WHEN** an import, declaration dependency, or alias targets an external name absent from the project-local index
- **THEN** the raw target remains representable while its indexed project-owned source and containment relationships stay constrained

#### Scenario: Database limit exceeded
- **WHEN** an unpublished generation crosses the configured database-size ceiling
- **THEN** the build fails with a resource diagnostic, removes the temporary generation, and leaves the prior database unchanged

#### Scenario: Oversized stored value
- **WHEN** a lexical or rendered value exceeds its finite storage limit
- **THEN** Ladon stores a bounded value with original-size and truncation evidence rather than allowing unbounded database growth

### Requirement: Honest freshness and incremental refresh
Every index generation MUST record source, import/declaration, toolchain, helper, and
schema fingerprints, and incremental refresh SHALL downgrade freshness when complete
invalidation cannot be established.

#### Scenario: Changed module refresh
- **WHEN** a module source fingerprint changes and recorded dependency fingerprints are complete
- **THEN** Ladon transactionally refreshes that module and invalidated dependents and reports the resulting generation as fresh

#### Scenario: Indirect import uncertainty
- **WHEN** an indirect imported declaration may have changed but the invalidation frontier is incomplete
- **THEN** Ladon reports `stale-indirect` or `partial` rather than fresh

#### Scenario: Toolchain incompatibility
- **WHEN** the pinned Lean/helper identity differs incompatibly from the stored generation
- **THEN** Ladon creates or requests a compatible generation and does not reuse rows as Lean-authoritative

### Requirement: Explicit proof-search scope
Queries SHALL support current namespace, direct imports, full transitive import
closure, project-owned declarations, external packages, and explicit root sets.

#### Scenario: Transitive closure scope
- **WHEN** a caller selects the complete transitive import closure of an owner
- **THEN** candidates include declarations reachable through the canonical module DAG subject to explicit ownership filters

#### Scenario: Multiple active roots
- **WHEN** a caller supplies an unfinished owner and authority modules as explicit roots
- **THEN** the effective scope is their deterministic union and records every root

### Requirement: Omission evidence
Ladon SHALL explain why modules or declarations are absent from an effective scope.

#### Scenario: Omitted declaration
- **WHEN** a known declaration is excluded by root reachability, package ownership, generated filtering, freshness, or missing elaborated evidence
- **THEN** the query response records the stable omission reason without treating it as no such declaration

### Requirement: Bounded query protocol and latency evidence
The index SHALL expose deterministic CLI and versioned JSON queries with bounded
result counts, timing, generation identity, and truncation metadata.

#### Scenario: Warm large-project query
- **WHEN** a benchmark executes a warm metadata query on the maintained large-project fixture
- **THEN** it returns within the packet's finite latency budget without rebuilding the target repository and records phase timings

#### Scenario: Repository indexes are materialized
- **WHEN** the umbrella acceptance run has writable Ladon and Matrix-Factorization checkouts
- **THEN** it creates or refreshes each checkout's disposable repository-local index and records generation identity, size, freshness, and cold/warm timings without committing the database
