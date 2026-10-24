# Spec Delta

## Purpose

Keep source-bound audit observations and attributed correspondence judgments visible through review and reporting, independently of formal proof support and mathematical falsity.

## ADDED Requirements

### Requirement: Preserve attributed findings
Investigation outputs SHALL retain reviewed statement discrepancies, method differences and unresolved/conflicting judgments with source bindings, evidence, attribution, dependencies and formal-support limits. Review completion SHALL NOT erase findings or imply mathematical falsity.

#### Scenario: Completed legacy mismatch
- **WHEN** a reviewed legacy claim records a mismatch and a different method
- **THEN** status and new terminal receipts preserve both dimensions as attributed findings without declaring the prose false

#### Scenario: Native review conflict
- **WHEN** native reviewers disagree or correct a first response
- **THEN** output retains the first response, correction and effective conflicting judgments separately
- **AND** a correction cannot change the original reviewer attribution

### Requirement: Capture observations before formal extraction
Users SHALL be able to capture, inspect and review immutable source-bound observations without a native formal counterpart. Pending or conflicting observations SHALL remain actionable; completed observation review SHALL preserve missing formal support.

#### Scenario: Observation-only review
- **WHEN** an exact source observation receives a resolved independent attributed review and its authored inventory is complete
- **THEN** the workflow can complete its recorded observation work while reporting incomplete formal correspondence and no established mathematical falsity

#### Scenario: Source drift
- **WHEN** the source, quotation, stored identity or response binding is altered
- **THEN** capture, inspection, review and reporting reject the invalid record

### Requirement: Reconcile supplementary report inputs
A report SHALL account for all findings and observations across compatible plans with the same original source scope, start time and budget. It SHALL preserve branch provenance and conflicts, reject conflicting immutable identities, and enforce input and output record bounds without resetting the clock.

#### Scenario: Supplementary observations survive
- **WHEN** two compatible plans contain distinct observations or different reviews of the same observation
- **THEN** the report retains every observation and attributed review with plan provenance, exposing disagreement and pending branches

#### Scenario: Incompatible or excessive inputs
- **WHEN** scope, original clock or budget differ, immutable identities collide, or combined bounds are exceeded
- **THEN** the report rejects the inputs instead of dropping evidence or normalizing identities

### Requirement: Keep coverage and historical authority explicit
Output SHALL distinguish authored source survey, argument review, formal support and mathematical falsity. New receipts SHALL identify their reporting projection. Existing valid historical receipts SHALL remain verifiable against their original projection without rewriting stored evidence.

#### Scenario: Survey-only coverage
- **WHEN** every inventory unit is surveyed but no argument claims or observations have been reviewed
- **THEN** output states the survey scope without implying whole-paper argument verification

#### Scenario: Historical receipt replay
- **WHEN** a valid earlier receipt is checked with unchanged plan, source and recorded clock
- **THEN** its historical projection remains verifiable while new receipts include the new findings projection

#### Scenario: Known development controls
- **WHEN** the two reference discrepancies and six successful local controls are exercised through the reporting path
- **THEN** both discrepancies remain visible, the two valid different-method controls remain supported locally, and no fresh discovery or whole-paper certification is claimed
