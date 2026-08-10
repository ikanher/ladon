## ADDED Requirements

### Requirement: Typed models are the only payload validation authority
Every registered native-v3 kind SHALL be validated by constructing its immutable typed payload model, and envelope dispatch SHALL NOT maintain a weaker parallel field validator.

#### Scenario: Malformed nested environment value
- **WHEN** a self-hashed environment artifact contains a numeric prover, array toolchain, empty dependency object, nonobject options, invalid trust value, or nonstring fingerprint scheme
- **THEN** validation rejects it with the kind model's stable stage, code, pointer, and message before projection

### Requirement: Complete closed nested schemas
Closed kind schemas SHALL validate the type, cardinality, identifier grammar, reference scope, and semantic enum of every core nested field.

#### Scenario: Invalid identifier container
- **WHEN** a claim or source-map identifier is numeric, an array, empty, or outside its typed grammar
- **THEN** no content artifact or SQLite row is accepted

### Requirement: Frozen Unicode contract
Canonicalization SHALL define deterministic behavior for valid Unicode scalars and SHALL convert invalid scalar strings into stable ProofIR diagnostics.

#### Scenario: Lone surrogate
- **WHEN** an input string contains a lone surrogate
- **THEN** validation returns the frozen ProofIR diagnostic rather than a raw runtime encoding exception

### Requirement: Independent ingestion bounds
Validation SHALL expose independent positive bounds for one artifact, an aggregate batch, and artifact count.

#### Scenario: Many valid artifacts
- **WHEN** every artifact is below `maxArtifactBytes`, the count is below `maxArtifacts`, and their aggregate is below `maxBatchBytes`
- **THEN** the batch is not rejected merely because the aggregate exceeds the single-artifact cap

### Requirement: Freeze-complete language-neutral corpus
The shared conformance corpus SHALL cover every registered artifact kind, nested value class, reference class, canonical identity seam, projection row family, query result family, bound, Unicode decision, and omission diagnostic needed by a second implementation.

#### Scenario: Rust readiness is evaluated
- **WHEN** any registered kind or required normalized/query family lacks a frozen valid and adversarial case
- **THEN** the semantic contract remains unfrozen and Rust work remains blocked

### Requirement: Corpus inventory is executable rather than descriptive
Every advertised adversarial coverage row SHALL resolve to a checked-in language-neutral vector whose exact validation and projection outcome is mechanically compared.

#### Scenario: Inventory names a missing mutation
- **WHEN** a corpus inventory row has no executable vector or expected stable diagnostic
- **THEN** the hardening exit class is partial and semantic freeze remains blocked

### Requirement: Core nested rows reject malformed values
Derivation, plan, attempt, check-run, attachment, governance, and source-map nested rows SHALL reject invalid identifiers, enums, container types, diagnostic values, evidence values, policy values, summaries, and coordinates according to one frozen typed model.

#### Scenario: r03 malformed mutation is replayed
- **WHEN** any of the nineteen unambiguously malformed r03 values is validated
- **THEN** it is rejected with the frozen stage, code, pointer, and message before projection
