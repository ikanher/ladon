## ADDED Requirements

### Requirement: Synthetic proof-surface witness fixtures
The system SHALL include portable synthetic fixtures that model the frozen spec,
proof endpoint, no-drift gate, source pin, and axiom audit pattern without
depending on pipeline-math, Quux, matrix-factorization, or any private sibling
repository.

#### Scenario: Fixture suite runs in repository tests
- **WHEN** the Ladon test suite runs without access to external Lean repositories
- **THEN** proof-surface witness normalization and route-audit tests use only repository-local synthetic fixtures

#### Scenario: Fixture uses nonstandard names
- **WHEN** a fixture models the proof-surface pattern with module names that are not `Theorems`, `Solution`, or `Discharge`
- **THEN** expected diagnostics are driven by explicit witness roles rather than hard-coded path names

### Requirement: Positive clean endpoint fixture
The system SHALL include a positive fixture where a public claim cites a
proof-backed endpoint with acceptable source attachment, clean no-drift gate
evidence, clean axiom audit evidence, and accurate nonclaims.

#### Scenario: Clean endpoint fixture is audited
- **WHEN** Ladon audits the positive proof-surface witness fixture
- **THEN** it emits or exposes `ladon.proof_surface.clean_endpoint` and does not emit spec-stub, missing-gate, missing-axiom, or suspicious-axiom diagnostics

### Requirement: Negative authority fixtures
The system SHALL include negative fixtures for spec-stub overclaims, missing
no-drift gates, missing axiom audits, suspicious axiom footprints, and proof
holes outside allowed quarantine.

#### Scenario: Spec stub overclaim fixture is audited
- **WHEN** a fixture claim cites a `lean_spec_stub` row as primary proof authority
- **THEN** Ladon emits `ladon.proof_surface.spec_stub_used_as_authority`

#### Scenario: Missing no-drift gate fixture is audited
- **WHEN** a fixture claim requires a spec-to-proof gate and no clean gate row is present
- **THEN** Ladon emits `ladon.proof_surface.missing_no_drift_gate`

#### Scenario: Missing axiom audit fixture is audited
- **WHEN** a fixture claim requires an axiom footprint and no accepted axiom audit row exists
- **THEN** Ladon emits `ladon.proof_surface.missing_axiom_audit`

#### Scenario: Suspicious axiom fixture is audited
- **WHEN** a fixture endpoint has a suspicious or unknown axiom in its audit row
- **THEN** Ladon emits `ladon.proof_surface.suspicious_axiom`

### Requirement: Weak attachment and stale pin fixtures
The system SHALL include fixtures showing that weak source attachment and stale
source pins do not satisfy high-confidence proof-surface route requirements.

#### Scenario: Weak endpoint attachment is audited
- **WHEN** a fixture endpoint joins only by basename, module/declaration name, or line anchor
- **THEN** Ladon preserves the weak attachment warning and does not classify the endpoint as clean

#### Scenario: Stale source pin is audited
- **WHEN** a fixture endpoint has a witness content hash that differs from Ladon declaration evidence
- **THEN** Ladon records stale source context and does not classify the endpoint as clean

### Requirement: Benchmark oracle coverage
The system SHALL define explicit expected outcomes for every promoted
proof-surface diagnostic and classification in the fixture suite.

#### Scenario: Oracles cover all proof-surface diagnostics
- **WHEN** the fixture tests run
- **THEN** they assert expected outcomes for spec-stub authority, missing no-drift gate, missing axiom audit, suspicious axiom, clean endpoint, and frozen spec hub cases

### Requirement: Fixture independence from Lean execution
The system SHALL make proof-surface route-audit fixtures replayable without
running Lean, while preserving quoted metadata that an external verifier would
have produced.

#### Scenario: Tests run without Lean binary
- **WHEN** the local environment lacks a Lean binary or external Lean package checkout
- **THEN** proof-surface fixture tests still exercise Ladon's witness normalization and route-audit behavior using frozen JSON and small source excerpts
