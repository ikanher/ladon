## ADDED Requirements

### Requirement: Review radar report
The system SHALL produce a reviewer-facing Review Radar report from before and
after Ladon report surfaces or atlas surfaces.

#### Scenario: Before and after reports are compared
- **WHEN** the user provides before and after Ladon report inputs for the same Lean project
- **THEN** the system emits a structured report containing changed modules, changed declarations, import-pressure deltas, evidence attachment deltas, review-priority roots, and nonclaims

#### Scenario: No before report is available
- **WHEN** the user provides only an after report
- **THEN** the system emits current-state review cards and marks changed-row sections as unavailable rather than inventing deltas

### Requirement: Review priority is explainable
The system SHALL present review priority as routing context with contributing
factors, not as a code-quality grade.

#### Scenario: Root receives high review priority
- **WHEN** a root receives high review priority
- **THEN** the report lists contributing factors such as changed theorem surfaces, import closure growth, finding count, proof-family clusters, packet evidence gaps, or low-confidence ProofIR joins

#### Scenario: Shared foundation appears hot
- **WHEN** a high-priority module is also a broad shared foundation
- **THEN** the report labels the result as review pressure and does not state that the module is bad or incorrect

### Requirement: Review radar trust boundary
The system SHALL include trust-boundary nonclaims in machine-readable and
reviewer-facing Review Radar output.

#### Scenario: Report includes structural observations
- **WHEN** Review Radar emits module, declaration, import, or reference observations
- **THEN** the report states that these observations route review and are not Lean kernel dependency, theorem-truth, proof-correctness, or witness-adequacy claims

#### Scenario: Report includes quoted external evidence
- **WHEN** Review Radar includes ProofIR or other external artifact status
- **THEN** the report marks the status as quoted external context with artifact identity when available

### Requirement: CI behavior is configurable
The system SHALL default to advisory output and SHALL fail CI only for explicitly
configured severe conditions.

#### Scenario: Advisory review run has high pressure
- **WHEN** Review Radar finds high review pressure without configured failure rules
- **THEN** the command exits successfully and records the pressure in the output

#### Scenario: Configured severe regression occurs
- **WHEN** a configured severe regression is detected
- **THEN** the command exits with failure status and records the exact rule that failed
