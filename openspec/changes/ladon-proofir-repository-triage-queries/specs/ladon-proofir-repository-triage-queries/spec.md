## ADDED Requirements

### Requirement: Repository triage exposes explicit evidence-health families
The system SHALL provide bounded SQL-first finding families for unattached surfaces, ambiguous attachments, stale attachments, missing/stale/failed replay, conditional conclusions, stale/unmatched witnesses, unsupported/malformed artifacts, and declaration-disconnected evidence.

#### Scenario: Mixed evidence-health repository
- **WHEN** a repository contains at least one member of every supported family
- **THEN** triage returns stable rule IDs, identities, reasons, source anchors, authorities, and family counts for each

### Requirement: Triage findings are advisory and actionable
The system SHALL describe the stored evidence condition, exact ownership evidence, and deterministic priority inputs without declaring a Lean theorem false or a conditional ProofIR claim defective.

#### Scenario: Conditional high-impact conclusion
- **WHEN** a conditional conclusion is reachable from many established premises
- **THEN** triage identifies the authority boundary and route impact while labeling the finding as review advice

#### Scenario: No exact owner
- **WHEN** an artifact has only basename or module proximity to declarations
- **THEN** no owner is selected and the weaker context is reported separately

### Requirement: Triage is bounded, indexed, and deduplicated
The system SHALL use parameterized indexed predicates, stable deduplication keys, per-family/global caps, deterministic ordering, and explicit truncation metadata.

#### Scenario: Repeated symptom
- **WHEN** one stale replay produces several related symptoms
- **THEN** stable findings cross-reference the shared evidence identity without duplicate rows for the same rule and subject

### Requirement: Triage reports its coverage
The system SHALL report which families were available, queried, empty, truncated, or unavailable for the active generation.

#### Scenario: DAG family unavailable
- **WHEN** no supported DAG was normalized
- **THEN** DAG-dependent triage reports unavailable or not-observed rather than zero defects
