## ADDED Requirements

### Requirement: Common native-v3 artifact envelope
Every ProofIR artifact SHALL use one exact envelope containing version, kind, detached content ID, producer, environment reference, subject references, coverage, payload, limitations, and namespaced extensions.

#### Scenario: Artifact-specific fields
- **WHEN** a derivation contains step-specific data
- **THEN** those fields occur under its version-locked payload rather than as unversioned top-level keys

### Requirement: Closed kind schemas
Validation SHALL dispatch only explicit supported v3 kind/version schemas and SHALL validate their complete payload and reference closure.

#### Scenario: Unknown native-looking kind
- **WHEN** an artifact declares version 3.0 and an unregistered `proofir.*` kind
- **THEN** validation rejects it with a stable unsupported-kind diagnostic before projection

### Requirement: Clean legacy rejection
Legacy ProofIR kinds and compatibility containers SHALL NOT be converted, ingested, or projected.

#### Scenario: Legacy artifact is discovered
- **WHEN** discovery encounters a former bridge, surface, replay, obligation-DAG, witness, or compatibility artifact
- **THEN** it emits one attributable legacy-unsupported diagnostic and contributes no semantic row

### Requirement: Deterministic canonical identity
Canonicalization SHALL produce identical bytes and detached content IDs across supported implementations for the shared corpus.

#### Scenario: Mutation after validation
- **WHEN** a caller mutates its source dictionary or a dictionary returned for serialization
- **THEN** the validated artifact and its content ID remain unchanged

### Requirement: Bounded stable validation
Validation SHALL bound input, output, nesting, collections, strings, and reference work and SHALL emit deterministic stage, code, pointer, and ordering.

#### Scenario: Output cap is exceeded
- **WHEN** a canonical or inspection result would exceed its configured output limit
- **THEN** no partial destination replaces the prior file and the terminal result reports the bound

### Requirement: Ordinary native tooling
The project SHALL expose validate, canonicalize, and inspect operations through the ordinary Ladon CLI and SHALL expose no ProofIR converter operation.

#### Scenario: Former converter invocation
- **WHEN** a caller requests the removed conversion operation
- **THEN** the CLI rejects the unsupported operation without reading or publishing an output artifact
