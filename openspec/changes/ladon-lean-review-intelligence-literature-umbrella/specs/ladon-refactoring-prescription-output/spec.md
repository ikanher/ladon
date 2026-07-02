## ADDED Requirements

### Requirement: Refactoring prescription rows
The system SHALL convert selected findings into refactoring prescription rows
that identify a proposed action, affected modules/declarations, source evidence,
confidence, and nonclaims.

#### Scenario: common-layer extraction candidate
- **WHEN** architecture policy and shared-dependency evidence show multiple peer groups importing the same module
- **THEN** Ladon emits an `extract_common_lower_layer` prescription with group evidence, importer count, confidence, and affected source modules

#### Scenario: bridge placement candidate
- **WHEN** a bridge-like module sits inside a peer namespace or a core module imports a bridge group
- **THEN** Ladon emits a `move_bridge_to_neutral_namespace` or `declare_explicit_bridge_policy` prescription with source path and import evidence

### Requirement: Prescription priority
The system SHALL prioritize prescriptions by combining available evidence such
as direct policy severity, source locations, fan-in/fan-out, root closure,
generated status, facade role, witness completeness, and confidence.

#### Scenario: severe direct boundary violation
- **WHEN** a core-looking direct peer import and a low-impact naming smell both exist
- **THEN** Ladon ranks the direct boundary prescription ahead of the naming-only prescription and reports the priority evidence

### Requirement: Prescription action taxonomy
The system SHALL use a stable action taxonomy for refactoring prescriptions so
CI, atlas, and reviewer-card consumers can group and filter recommendations.

#### Scenario: generated artifact pressure
- **WHEN** a finding concerns duplicate generated imports or generated naming pressure
- **THEN** Ladon emits a generator-focused prescription such as `clean_generator_output` or `move_generated_parameters_to_manifest`

#### Scenario: missing trust evidence
- **WHEN** a public claim route lacks required proof-surface witness evidence
- **THEN** Ladon emits an `add_proof_surface_witness_evidence` prescription that points to existing proof-surface diagnostics

### Requirement: Prescriptions are not automatic rewrites
The system SHALL state that prescription rows are review guidance and SHALL NOT
apply code moves, import removals, or proof edits unless a separate explicit
autofix capability is implemented and invoked.

#### Scenario: prescription appears in output
- **WHEN** a refactoring prescription is rendered
- **THEN** the output states that Ladon is recommending review direction from evidence, not changing source code or proving the proposed refactor is correct
