# proofir-content-environment-and-subject-identity Specification

## Purpose
TBD - created by archiving change proofir-content-environment-and-subject-identity. Update Purpose after archive.
## Requirements
### Requirement: Separate content and observation identities
The system SHALL distinguish canonical content artifact identity from path/generation observation identity and SHALL keep unchanged content stable across database generations.

#### Scenario: Unchanged artifact in a new generation
- **WHEN** identical canonical artifact bytes are discovered under a new generation
- **THEN** the content artifact ID remains equal and the observation ID changes

### Requirement: Non-self-referential canonical hashing
Artifact identity SHALL be computed by a specified detached-ID canonicalization transform and validators SHALL recompute it.

#### Scenario: Embedded ID is altered
- **WHEN** an envelope's declared artifact ID differs from the recomputed detached digest
- **THEN** validation rejects the identity at the envelope stage

### Requirement: Exact environment references
Semantic subject identity SHALL reference a content-addressed environment manifest containing prover/toolchain, dependency, compiled-module, option, trust, and fingerprint-scheme identities.

#### Scenario: Toolchain changes
- **WHEN** a declaration name and display text are unchanged but its Lean toolchain identity changes
- **THEN** the environment reference and environment-scoped declaration identity differ

### Requirement: Typed subject references
The system SHALL represent statements, declarations, source surfaces, artifacts, derivation steps, and local contexts as tagged subject references rather than untyped strings.

#### Scenario: Claim and node share a local spelling
- **WHEN** two artifacts both contain local ID `claim.root`
- **THEN** no semantic join occurs without an explicit artifact-scoped typed reference

### Requirement: Opaque Lean identity profile
Lean workers SHALL produce versioned declaration and expression fingerprints, while core readers SHALL validate their structure without implementing Lean term semantics.

#### Scenario: Unknown Lean fingerprint scheme
- **WHEN** a subject uses an unsupported Lean fingerprint scheme
- **THEN** the core retains it as unsupported opaque evidence and does not compare it as an exact statement identity
