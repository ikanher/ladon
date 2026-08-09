## ADDED Requirements

### Requirement: Conformance-gated Rust workspace
Rust implementation SHALL begin only after the v3 corpus freezes canonical bytes, digests, diagnostics, validation stages, and normalized rows.

#### Scenario: Corpus is not frozen
- **WHEN** canonical fixture expectations are still changing without a version bump
- **THEN** Rust production integration remains blocked

### Requirement: Cross-language canonical parity
Rust and Python SHALL produce byte-identical canonical artifacts and identical content IDs for every accepted corpus fixture.

#### Scenario: Canonical corpus run
- **WHEN** both implementations process the canonical corpus
- **THEN** every byte output and digest agrees

### Requirement: Validation and diagnostic parity
Rust and Python SHALL agree on accepted/rejected stages, stable diagnostic codes, JSON pointers, and retained partial evidence.

#### Scenario: Missing reference fixture
- **WHEN** both validators inspect the same reference-invalid artifact
- **THEN** they return the same stage, diagnostic code, and pointer

### Requirement: Typed opaque Lean boundary
Rust SHALL treat Lean declaration, expression, substitution, and local-context payloads as versioned opaque typed records and SHALL NOT implement Lean elaboration or definitional equality.

#### Scenario: Lean fingerprint is compared
- **WHEN** Rust compares two Lean statement references
- **THEN** it uses scheme/environment/fingerprint identity without parsing Lean terms

### Requirement: SQLite projection parity
Rust and Python projections SHALL produce equivalent artifact-scoped normalized rows, coverage, omissions, query results, and authority boundaries on the shared corpus without silent replacement.

#### Scenario: Dossier parity
- **WHEN** both projections serve the same theorem dossier fixture
- **THEN** normalized deterministic result payloads agree

### Requirement: No research-repository dependency
The Rust workspace and its tests SHALL NOT import, build, execute, or require Quux.

#### Scenario: Isolated CI
- **WHEN** Rust CI runs with only this repository and declared package dependencies
- **THEN** the full conformance suite passes
