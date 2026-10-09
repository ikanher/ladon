## Purpose
Refresh changed lexical source material without repeatedly extracting unchanged modules, while preserving coherent index generations and stored-evidence authority.

## ADDED Requirements

### Requirement: Incremental update is explicit
An explicit index update operation SHALL report its base generation, observed changes, extraction reuse, output generation and resource costs. Searches and status SHALL NOT initiate updates. Missing or incompatible bases SHALL report that a full build is required without silently performing one.

#### Scenario: One module is added
- **WHEN** a compatible index receives an explicit update after one supported module is added
- **THEN** the published generation contains its declarations and the report distinguishes reused modules from newly extracted modules

#### Scenario: Incompatible schema or configuration
- **WHEN** the base schema, toolchain or extraction configuration cannot safely support incremental reuse
- **THEN** update leaves the base usable and reports a full-build-required reason and an explicit build command

### Requirement: Updated lexical results equal a clean build
For the same stable supported inputs, incremental update SHALL produce the same lexical declaration, import, scope and name/type-search results and generation identity as a clean build. Physical database layout, process receipts and timings need not be identical.

#### Scenario: Add edit delete rename and change imports
- **WHEN** an update processes added, changed, removed and renamed modules including changed imports
- **THEN** comparison with a clean build finds no obsolete declarations, duplicate postings or incorrect scope membership

#### Scenario: No input changes
- **WHEN** explicit update observes no changes
- **THEN** it reports a no-op with the existing identity and does not re-extract or replace the database

### Requirement: Publication protects existing readers and writers
Update SHALL publish atomically under the existing destination ownership policy, revalidate its source snapshot before publication and preserve the previous database on handled failure. Existing readers SHALL see one complete generation. Concurrent publishers SHALL receive a clear busy outcome rather than corrupting shared state.

#### Scenario: Writer and source mutation overlap
- **WHEN** another publisher owns the destination or sources change during update
- **THEN** update terminates with a specific busy or source-changed result, publishes no mixed generation and does not retry indefinitely

#### Scenario: Budget or integrity failure
- **WHEN** storage, integrity or publication validation fails
- **THEN** the prior generation remains queryable and the operation emits a terminal failure with configured and observed limits

### Requirement: Lexical updates preserve evidence meaning
An update SHALL NOT rebind stored semantic, lineage or ProofIR evidence to newly observed source identities. It SHALL preserve that evidence under its original ownership with explicit stale/unavailable associations, or reject unsupported updates before publication. Lexical refresh SHALL NOT invoke Lean or certify compilation.

#### Scenario: A source with stored lineage changes
- **WHEN** lexical update changes the owner source of a stored theorem closure
- **THEN** the closure cannot become fresh evidence for the changed source merely because lexical publication succeeded

### Requirement: Incremental reuse has a measured cost benefit
Acceptance SHALL include complete ordinary before/after measurements on a declared workload with a small source delta, identical lexical outcomes and reported wall time, extraction counts, RSS, final bytes and temporary disk use. Measurements SHALL distinguish full source hashing from repeated extraction and preserve every sample.

#### Scenario: Update is dominated by database copying
- **WHEN** reuse saves extraction but produces no material end-to-end improvement
- **THEN** the result is recorded as a failed investment gate and the package remains deferred rather than labelled a successful incremental optimization
