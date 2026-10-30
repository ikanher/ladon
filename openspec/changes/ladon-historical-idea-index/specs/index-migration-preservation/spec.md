# Spec Delta

## Purpose

Upgrade an existing index while measuring preservation of its contents, associations, authority and query behavior before publication.

## ADDED Requirements

### Requirement: Migration SHALL preserve existing evidence
An additive migration SHALL preserve every existing table's protected columns and rows except exact declared metadata substitutions. Counts alone SHALL NOT establish preservation. Existing authority and proof freshness SHALL NOT be promoted.

#### Scenario: Swapped associations
- **WHEN** a candidate migration swaps dependency endpoints without changing counts
- **THEN** the preservation metric fails and publication is blocked

### Requirement: Migration metrics SHALL report their coverage
The metric SHALL report hard violations, checked and failed data/link/query invariants, and storage ratio. Zero observations SHALL be reported as unassessed, not perfect coverage. Historical enrichment SHALL be reported separately.

#### Scenario: No query samples
- **WHEN** no query observations are supplied
- **THEN** the query-loss fraction is null and its checked count is zero

### Requirement: Migration SHALL publish atomically
Migration SHALL hold the existing publication lock, validate a temporary copy and preserve a recoverable pre-migration snapshot. Failure before replacement SHALL leave the original database unchanged. A durability failure after replacement SHALL be reported as uncertain rather than as an unchanged database.

#### Scenario: Injected validation failure
- **WHEN** migration validation fails before replacement
- **THEN** the original database remains byte-identical and queryable

### Requirement: Metadata migration SHALL not execute proof tooling
Historical metadata migration SHALL neither invoke Lean nor refresh lexical or semantic proof projections. Supported older snapshots SHALL remain readable with their original evidence identities.

#### Scenario: Evidence-bearing index
- **WHEN** a v6 index containing stored lineage and semantic evidence is migrated
- **THEN** those records remain unchanged and supported stored queries retain their prior result
