## MODIFIED Requirements

### Requirement: Orthogonal evidence dimensions
Assertion state, semantic validation, attachment result, replay relationship, coverage, execution binding, observation state, operation outcome, source freshness, environment match, authority basis, analysis completeness, and guarantee scope SHALL remain independently represented. No field SHALL be derived solely from a stronger-looking value on another axis.

#### Scenario: Fresh source with unchecked claim
- **WHEN** an exact fresh attachment refers to an unchecked producer assertion and no checker ran
- **THEN** the result reports exact attachment and fresh source with absent observation, not-run outcome, no execution binding, and no semantic acceptance

#### Scenario: Pinned executable with stored observation
- **WHEN** the current explicit toolchain matches a previously successful stored observation but no new check runs
- **THEN** execution history remains attributable while observation state is stored and the result does not report fresh live authority

#### Scenario: Authoritative live check with partial analysis
- **WHEN** an explicitly selected pinned checker accepts its exact application subject but a registered downstream analysis is truncated
- **THEN** the result preserves explicit-pinned execution and elaborator-check basis while reporting partial analysis completeness

### Requirement: Exact checker observations
Accepted checker observations SHALL include checker identity, executable or implementation identity, exact execution-context identity, toolchain-selection mode, environment, exact inputs, operation, per-subject results, output digests, bounds, guarantee, and independent evidence dimensions; only the exact fresh operation SHALL receive live observation state.

#### Scenario: Lean declaration accepted
- **WHEN** a pinned Lean worker confirms one declaration in one environment
- **THEN** the observation's guarantee applies only to that declaration, operation, and environment

#### Scenario: Candidate application accepted
- **WHEN** a pinned Lean worker elaborates one candidate application against one goal and reports residual premises
- **THEN** authority attaches to that exact application result and does not claim declaration-proof replay or acceptance of the residual goals

#### Scenario: Preflight environment differs from execution
- **WHEN** executable identity or version was inspected under an environment other than the recorded worker environment
- **THEN** the check is invalid and cannot receive explicit-pinned execution binding or accepted authority

#### Scenario: Successful observation is reloaded
- **WHEN** a previously successful checker observation is read from an artifact or SQLite projection without a new checker launch
- **THEN** it is labeled stored evidence and is not reported as a fresh live observation

## ADDED Requirements

### Requirement: Evidence transitions are explicit and non-escalating
Every projection, persistence round trip, dossier, renderer, and aggregate SHALL apply a total registered transition table and SHALL preserve or weaken execution binding, observation state, operation outcome, source freshness, environment match, authority basis, and analysis completeness.

#### Scenario: Ambient evidence is projected
- **WHEN** a parent result has ambient-observed execution binding
- **THEN** no child projection may report explicit-pinned execution binding

#### Scenario: Evidence is absent
- **WHEN** a parent has absent observation state and not-run outcome
- **THEN** no child projection may report live/stored observation or accepted outcome without a separately attributable check

#### Scenario: Source is stale or environment mismatched
- **WHEN** a parent reports stale source or mismatched environment
- **THEN** no child projection may report fresh source or exact environment match

### Requirement: Analysis completeness uses a closed explicit state
Live checks and derived evidence summaries SHALL report analysis completeness as exactly `complete`, `partial`, `invalid`, or `not-assessed`, derived from registered required populations, operation validity, omissions, residuals, and bounds.

#### Scenario: Optional analysis was not run
- **WHEN** no derivation, coverage, or residual analysis was requested or executed
- **THEN** its completeness is `not-assessed` rather than complete

#### Scenario: Required population is truncated
- **WHEN** any registered population required by a summary is truncated or unavailable
- **THEN** the summary cannot report complete analysis

#### Scenario: Invalid child result enters an aggregate
- **WHEN** any required child result is invalid
- **THEN** the aggregate cannot report complete analysis even if all other children are complete
