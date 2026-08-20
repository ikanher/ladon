## MODIFIED Requirements

### Requirement: Orthogonal evidence dimensions
Assertion state, semantic validation, freshness, attachment result, replay relationship, coverage, source/check authority, analysis completeness, and guarantee scope SHALL remain independently represented.

#### Scenario: Fresh source with unchecked claim
- **WHEN** an exact fresh attachment refers to an unchecked producer assertion
- **THEN** the result reports exact attachment and fresh source without reporting semantic acceptance

#### Scenario: Authoritative live check with partial analysis
- **WHEN** an explicitly selected pinned checker accepts its exact application subject but a registered downstream analysis is truncated
- **THEN** the result preserves the application-check authority while reporting partial analysis completeness

### Requirement: Exact checker observations
Accepted checker observations SHALL include checker identity, executable or implementation identity, toolchain-selection mode, environment, exact inputs, operation, per-subject results, output digests, bounds, and guarantee; only the exact fresh operation SHALL receive its live authority classification.

#### Scenario: Lean declaration accepted
- **WHEN** a pinned Lean worker confirms one declaration in one environment
- **THEN** the observation's guarantee applies only to that declaration and environment

#### Scenario: Candidate application accepted
- **WHEN** a pinned Lean worker elaborates one candidate application against one goal and reports residual premises
- **THEN** authority attaches to that exact application result and does not claim declaration-proof replay or acceptance of the residual goals

#### Scenario: Successful observation is reloaded
- **WHEN** a previously successful checker observation is read from an artifact or SQLite projection without a new checker launch
- **THEN** it is labeled stored evidence and is not reported as fresh live authority

## ADDED Requirements

### Requirement: Analysis completeness uses a closed explicit state
Live checks and derived evidence summaries SHALL report analysis completeness as exactly `complete`, `partial`, `invalid`, or `not-assessed`, derived from registered required populations, operation validity, omissions, and bounds.

#### Scenario: Optional analysis was not run
- **WHEN** no derivation, coverage, or residual analysis was requested or executed
- **THEN** its completeness is `not-assessed` rather than `complete`

#### Scenario: Required population is truncated
- **WHEN** any registered population required by a summary is truncated or unavailable
- **THEN** the summary cannot report `complete`

### Requirement: Evidence projections are non-escalating
A projection, persistence round trip, dossier, renderer, or aggregate summary SHALL preserve or weaken source/check authority and analysis completeness and SHALL never strengthen either dimension from partial, invalid, ambient, stored, or absent evidence.

#### Scenario: Partial coverage enters a dossier
- **WHEN** a dossier combines accepted stored evidence with partial theorem-scoped coverage
- **THEN** the dossier retains stored-evidence authority and reports partial completeness without promoting either dimension

#### Scenario: Invalid child result enters an aggregate
- **WHEN** any required child result is invalid
- **THEN** the aggregate cannot report complete analysis even if all other child results are complete

