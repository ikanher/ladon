## ADDED Requirements

### Requirement: ProofIR evidence is exposed through ordinary installed CLI commands
The system SHALL expose catalog status, theorem evidence, artifact evidence, and
bounded obligation routes through the existing installed Ladon command families
with caller-neutral names and no LLM-specific command or protocol.

#### Scenario: Installed help
- **WHEN** a user requests help for the relevant index, theorem, and ProofIR evidence operations
- **THEN** the supported selectors, directions, refresh policy, bounds, formats, outputs, and nonclaims are documented

#### Scenario: Warm read-only query
- **WHEN** the database and requested evidence are fresh
- **THEN** the command reads the stored database without invoking Lean, replay commands, external checkers, or artifact generators

#### Scenario: Missing configured evidence
- **WHEN** a project has no configured ProofIR inputs
- **THEN** the command returns an explicit unavailable/not-configured result and the documented non-error or error exit class

### Requirement: Build and status expose ProofIR generation state
The system SHALL integrate configured ProofIR inputs into index build identity
and SHALL report catalog, normalized, unsupported, malformed, stale, surface,
replay, DAG, attachment, and omission counts without claiming exhaustiveness
beyond configured inputs.

#### Scenario: Two-build persistence
- **WHEN** an unchanged project with configured artifacts builds the index twice
- **THEN** the second canonical database retains equivalent ProofIR identities and query results

#### Scenario: Configured artifact changes
- **WHEN** artifact bytes change after a build
- **THEN** status reports stale ProofIR generation and a query follows the explicit refresh/refusal policy

### Requirement: Text and JSON render the same evidence contract
The system SHALL build versioned render-neutral results and SHALL render
equivalent text and JSON with source links, artifact identity, status,
authority, freshness, diagnostics, coverage, and truncation.

#### Scenario: Surface plus replay evidence
- **WHEN** a theorem evidence query finds a surface and exact replay provenance
- **THEN** both formats show the extractor boundary and replay run separately and neither promotes theorem status

#### Scenario: Mixed-authority route
- **WHEN** an obligation route crosses established and conditional obligations
- **THEN** both formats show every authority/status transition and the conditional conclusion

#### Scenario: Output byte cap
- **WHEN** a rendered result exceeds the configured output limit
- **THEN** the command follows the documented bounded-result behavior without emitting corrupt partial JSON

### Requirement: Portable TDD covers the complete workflow
The system SHALL land failing portable tests before implementation for catalog
generation, surfaces/replay, DAG routes, declaration ambiguity, lineage overlay,
staleness, unsupported input, constraints, indexes, rebuilds, CLI, and rendering.

#### Scenario: End-to-end portable fixture
- **WHEN** the fixture runs index build, configured artifact ingestion, status, theorem evidence, and obligation-route queries
- **THEN** exact expected rows and renderings pass without reading a sibling repository

#### Scenario: Failure matrix
- **WHEN** malformed, stale, ambiguous, cyclic, oversized, and unsupported fixtures run
- **THEN** each produces its specified diagnostic/exit class and preserves database integrity

### Requirement: Real calibration evaluates answer quality rather than lookup speed
The system SHALL provide opt-in fingerprinted calibration for Quux and
Matrix-Factorization and SHALL separate observations from portable correctness
gates.

#### Scenario: Quux surface/replay quality oracle
- **WHEN** calibration reads the current supported Quux surface and replay artifacts
- **THEN** it reports the observed related/unobserved coverage and verifies that one stored query reconstructs the cross-artifact evidence chain

#### Scenario: CDC route quality oracle
- **WHEN** calibration queries the CDC obligation DAG
- **THEN** it returns representative paper-conditional and Lean-premise routes with correct boundary transitions

#### Scenario: Duplicate-name quality oracle
- **WHEN** calibration samples duplicated Matrix-Factorization declaration candidates
- **THEN** no name-only candidate is selected without compatible source evidence

#### Scenario: Performance interpretation
- **WHEN** timings are recorded
- **THEN** the report compares warm DB queries with structured JSON lookup but does not declare success from latency alone

### Requirement: Documentation and skill preserve operational boundaries
The system SHALL update README, CLI and architecture documentation, and the
authoritative Ladon skill to describe configuration, rebuilds, queries,
coverage, authority, and nonclaims using actual installed commands.

#### Scenario: Documentation verification
- **WHEN** documentation and skill command examples run against an installed wheel
- **THEN** every command is accepted and uses the same project-local database

#### Scenario: Architecture audit
- **WHEN** the completed implementation is audited
- **THEN** it contains no second database, raw-dialect semantic mirror, hidden external execution, arbitrary first-match attachment, or ProofIR-to-Lean authority promotion
