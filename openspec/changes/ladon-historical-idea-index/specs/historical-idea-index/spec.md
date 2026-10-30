# Spec Delta

## Purpose

Track the historical development of mathematical ideas independently of Lean implementation dates and proof evidence authority.

## ADDED Requirements

### Requirement: Historical dates SHALL be evidence-labelled
Every historical date projection SHALL expose an exact year, decade estimate, precision, status and basis. Unknown dates SHALL remain explicitly unknown. Competing claims SHALL remain available and at most one reviewed attribution per idea SHALL be selected.

#### Scenario: Exact year and estimate differ
- **WHEN** a catalogue contains a source-backed 1951 attribution and a reviewed 1940s estimate for different ideas
- **THEN** queries expose the exact year for the first and a decade estimate for the second, without converting the estimate into an exact year

#### Scenario: No dating evidence exists
- **WHEN** a declaration has no historical correspondence
- **THEN** its historical projection reports unassessed status and null dates

### Requirement: Historical correspondence SHALL survive declaration refresh
Authored links SHALL identify their declaration and statement fingerprint independently of disposable index row IDs. A changed, missing or ambiguous statement SHALL retain an unresolved or stale link rather than inherit reviewed correspondence.

#### Scenario: Same name changes proposition
- **WHEN** a linked declaration retains its name but its indexed statement changes
- **THEN** the historical link remains recorded and is marked stale

### Requirement: Historical prerequisite graphs SHALL be acyclic
Historical prerequisite edges SHALL be separate from formal dependencies and bibliographic citations. Catalogue acceptance SHALL reject self-dependencies and directed cycles atomically.

#### Scenario: Cyclic catalogue
- **WHEN** a proposed catalogue contains a directed cycle
- **THEN** synchronization fails and the previous catalogue remains intact

### Requirement: Historical indexing SHALL be reproducible
The system SHALL ingest a versioned authored catalogue, validate its fields and references, and preserve a separate historical input fingerprint. Rebuilds SHALL reproduce the catalogue without deriving dates from source timestamps or theorem names.

#### Scenario: Rebuild with the same catalogue
- **WHEN** the same Lean sources and historical catalogue are indexed again
- **THEN** the historical records and resolved correspondences agree
