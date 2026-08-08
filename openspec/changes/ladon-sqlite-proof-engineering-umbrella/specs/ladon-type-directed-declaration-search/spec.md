## ADDED Requirements

### Requirement: Type search is scoped and fresh
`proof-search search type` SHALL validate the module and requested scope, preserve source-only omissions, and by default require agreement among repository, index, and Lean-worker generations.

#### Scenario: Semantic generation is stale
- **WHEN** current repository or worker identity differs from the semantic index
- **THEN** verified type search fails closed unless the caller explicitly requests stored-only candidate diagnostics

### Requirement: SQLite shortlisting precedes Lean verification
The query SHALL combine bounded exact-fingerprint, head/arity, shape, constant-overlap, and semantic-FTS buckets, applying scope and ownership filters in SQL before one batched Lean candidate check.

#### Scenario: Candidate cap is smaller than index
- **WHEN** the repository contains more structural candidates than the cap
- **THEN** the result records bucket/cap omissions and checks no more than the declared number in Lean

### Requirement: Results contain only verified matches by default
The `ladon-proof-search-type-result-v1` `results` collection SHALL default to Lean-verified applications and preserve declaration location, type, substitutions, residuals, unresolved goals, authority, freshness, ranking, coverage, bounds, and nonclaims.

#### Scenario: Structural near-match fails in Lean
- **WHEN** SQLite shortlists a declaration but Lean rejects all configured passes
- **THEN** it is absent from default results and appears only in explicitly bounded diagnostic rejection output

### Requirement: Ranking is deterministic and explainable
Verified results MUST use the documented lexicographic cost vector and fully qualified name tie-break and MUST expose both vector and explanation.

#### Scenario: Equivalent candidates tie semantically
- **WHEN** two candidates have identical semantic and scope costs
- **THEN** their fully qualified names determine stable order
