## ADDED Requirements

### Requirement: Module readiness report
The system SHALL produce module-readiness rows that summarize Lean module
boundary pressure using module DAG evidence, source paths, facade metadata,
namespace observations when available, and optional module-system witness rows.

#### Scenario: broad facade pressure is reported
- **WHEN** a root or facade module imports a broad implementation closure
- **THEN** Ladon reports a module-readiness row with the module name, import count or closure evidence, facade subtype if known, and a review-oriented nonclaim

#### Scenario: module-readiness evidence is absent-safe
- **WHEN** no Lean module-system witness is supplied
- **THEN** Ladon still reports text-backed module DAG readiness rows and labels module-system-specific fields as unavailable rather than inferred

### Requirement: Namespace and module drift classification
The system SHALL distinguish Lean module paths from Lean namespaces and report
namespace/module drift as review pressure rather than as an error.

#### Scenario: declaration namespace differs from module path
- **WHEN** declaration extraction observes declarations in a namespace that does not align with the importing module path
- **THEN** Ladon reports the drift with source evidence and labels it as conceptual organization pressure, not a Lean correctness failure

### Requirement: Public/private boundary hints
The system SHALL classify candidate public API, implementation, bridge, common,
and generated modules when enough source or policy evidence exists.

#### Scenario: implementation module acts like public API
- **WHEN** a non-facade implementation module has high fan-in or broad root exposure
- **THEN** Ladon emits a module-readiness hint suggesting facade promotion, API split, or common-layer review with the evidence used

#### Scenario: explicit role suppresses severity
- **WHEN** policy or metadata marks a module as an intentional public facade, bridge, common layer, or generated aggregation module
- **THEN** Ladon preserves the row but lowers or reclassifies severity according to that role instead of treating it as ordinary coupling

### Requirement: Module-system witness authority
The system SHALL keep optional Lean module-system witness rows separate from
text-backed module heuristics and SHALL include backend, tool version, command,
and confidence metadata for every such row.

#### Scenario: module-system witness exists
- **WHEN** a witness says an import or declaration is public, private, exposed, or module-system checked
- **THEN** Ladon reports that status as quoted Lean-owned evidence with the witness metadata

#### Scenario: weak witness exists
- **WHEN** a module-system witness lacks source hash, command, backend, or tool version metadata
- **THEN** Ladon labels the row low-confidence and does not use it to clear module-readiness warnings
