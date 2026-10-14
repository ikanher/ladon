# Spec Delta

## Purpose

Make local correspondence checking usable through one ordinary investigation
workflow and evaluate its actual contribution with preserved, independently scored evidence.

## ADDED Requirements

### Requirement: One public authoring and checking path
The ordinary CLI SHALL accept source-bound interpretations and selected formal evidence, generate obligations, execute bounded supplied checks, and inspect remaining work. Authored records SHALL directly produce native evidence so users need not retype the same mathematics into a separate ledger.

#### Scenario: A reviewer completes a local comparison
- **WHEN** its interpretation, selected formal application, and check results are recorded through the public path
- **THEN** inspection, challenge export, and the next-work queue reference the same immutable subjects and evidence

### Requirement: Backward-compatible opt-in operation
Structured correspondence SHALL be opt-in while existing investigation v1/v2 behavior and native artifacts retain their contracts. Unsupported new native kinds SHALL fail explicitly in consumers without support. Copying old free-text records SHALL NOT grant structured or checked authority.

#### Scenario: Existing investigation is reopened
- **WHEN** a version-two plan is inspected with the new release
- **THEN** its previous semantics remain available and no checked correspondence is inferred from its text fields

### Requirement: Independent review preserves original responses
Challenge export SHALL include required source context and obligations while excluding prior assessments, repairs, and answer metadata. First responses SHALL remain immutable; changed contexts require an actual newly bound review. Attribution labels SHALL NOT be presented as verified identity or isolation.

#### Scenario: Reviewer corrects a local classification
- **WHEN** independent review changes the author's assessment
- **THEN** the first responses remain preserved and reconciliation is recorded separately with current subject bindings

### Requirement: Actionable scoped completion
The workflow SHALL prioritize unresolved local correspondence obligations while retaining unexamined sources and other pending work. It SHALL distinguish mathematical review from formal correspondence, and SHALL report budgets, missing inputs, and unsupported operations without fictitious counterparts or success by record count.

#### Scenario: Conventional review finishes without a formal counterpart
- **WHEN** all reviewed mathematical steps are resolved but no formal evidence exists for an alignment
- **THEN** the result reports the completed review dimension and incomplete formal-correspondence dimension separately

### Requirement: Native consumer failures remain observable
Successful public output SHALL retain valid native evidence and authority distinctions through rendering and projection. A failed producer, unsupported advertised option, or malformed reserved evidence container SHALL report its actual failure without silently falling back to weaker output as equivalent success.

#### Scenario: Rendering encounters an invalid evidence container
- **WHEN** a payload violates the reserved evidence-container contract
- **THEN** the failure is retained with a diagnostic and no successful native correspondence report is claimed

### Requirement: Predeclared comparative evaluation
Evaluation SHALL freeze inputs, justified reference outcomes, budgets, configurations, and scoring before fresh auditor dispatch. Assisted and ordinary-tool runs SHALL receive matched primary inputs and resource policies. First responses, corrections, false alarms, abstentions, omitted work, and costs SHALL be reported separately from development-case success.

#### Scenario: Assistance finds no additional justified faults
- **WHEN** the assisted arm matches or underperforms ordinary auditing
- **THEN** the evaluation preserves that result and does not infer detection benefit from passing implementation tests or adding more records

#### Scenario: Aggregate scoring disagrees with case rows
- **WHEN** case classifications are serialized for evaluation
- **THEN** normalized per-case verdicts determine aggregate counts mechanically and inconsistent aggregates are rejected or corrected in a separate record

### Requirement: Portable operation and explicit provenance
The consuming workflow SHALL operate without Quux, a model account, or an external paper checkout in its portable tests. External real-source qualifications SHALL record actual local Ladon imports, source identities, target toolchain, input access, and setup costs.

#### Scenario: Only an older installed Ladon is on PATH
- **WHEN** qualification is intended to exercise the current development checkout
- **THEN** the run verifies checkout import identities and does not use the older executable as evidence for new behavior
