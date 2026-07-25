# ladon-openspec-state-reconciliation Specification

## Purpose
TBD - created by archiving change ladon-openspec-state-reconciliation. Update Purpose after archive.
## Requirements
### Requirement: Evidence-backed reconciliation ledger
Every legacy status or archive decision SHALL be recorded with disposition,
source/test/gate evidence, authoritative owner, residual owner and replacement
if any, and archive outcome. The ledger SHALL reference, not duplicate, the
alpha umbrella's lifecycle dependencies.

#### Scenario: Packet marked complete
- **WHEN** a packet's unchecked tasks are reconciled as already implemented
- **THEN** the ledger names the source and tests proving each requirement before task/status changes

#### Scenario: Insufficient evidence
- **WHEN** implementation evidence does not cover a packet requirement
- **THEN** the packet remains active with a narrowed residual task instead of being marked complete

### Requirement: Stale active packet disposition
The reconciliation SHALL inspect the seven identified pre-program candidate
packets and SHALL complete, supersede-with-residuals, retain, or block each
based on evidence rather than umbrella checkboxes alone.

#### Scenario: Split proof-xray ownership
- **WHEN** proof-xray roadmap requirements are reconciled
- **THEN** staging retains quoted witness/trust rows, alpha declaration extraction owns direct Lean statement/type/value dependency and axiom/sorry/unsafe facts, and the narrowed proof-xray roadmap owns any future tactic-skeleton/InfoTree evidence contract without inventing a native-generation requirement

#### Scenario: Residual generated fan-in defect
- **WHEN** generated-attribution evidence does not cover the reproduced importer-population defect
- **THEN** that residual requirement is transferred to the alpha signal owner before the old packet is recorded as superseded-with-residuals

#### Scenario: Residual benchmark obligation
- **WHEN** portable oracle work does not cover a review-signal benchmark requirement
- **THEN** uncovered positive/negative fixtures, including source-pattern and claim-authority boundaries, and metric/drift obligations are transferred to the alpha benchmark owner before the legacy packet is recorded as superseded-with-residuals

### Requirement: Unique future-lane ownership
Reconciliation SHALL assign non-duplicated authoritative scopes along the chain
alpha declaration extraction → bounded theorem-surface changelog child → future
Review Radar MVP child under the retained planning umbrella, while preserving
the narrower authority of proof-xray staging.

#### Scenario: Theorem extraction ownership
- **WHEN** the future semantic changelog needs theorem statement data
- **THEN** it consumes the alpha elaborated-declaration surface rather than defining a parallel extractor

#### Scenario: Review Radar backlog
- **WHEN** Review Radar remains unimplemented
- **THEN** its planning umbrella stays active outside the alpha critical path, implementation checkboxes are removed from it, and implementation is deferred to a separately bounded MVP child

#### Scenario: Planning-umbrella delta specs
- **WHEN** the retained Review Radar planning umbrella overlaps concrete changelog or proof-xray extraction requirements
- **THEN** concrete semantic changelog requirements move to the bounded theorem child and optional x-ray consumer requirements reference, rather than duplicate, their staging/declaration/future-x-ray owners

### Requirement: Strict packet validity
Active and completed-unarchived packets MUST pass strict validation or have an
explicit ledger blocker and repair task.

#### Scenario: Invalid completed ProofIR packet
- **WHEN** a completed packet lacks required delta specs
- **THEN** reconciliation repairs the artifact or records and executes a validated superseding archive path

### Requirement: Conflict-aware archive batches
Completed changes SHALL be archived in reviewed dependency batches, and
canonical specs SHALL be validated after each batch.

#### Scenario: Conflicting delta requirements
- **WHEN** two completed changes would write incompatible requirements to the same canonical capability
- **THEN** archiving stops until the ledger records the chosen authoritative requirement and resolution

#### Scenario: Successful batch
- **WHEN** a batch validates with no unresolved conflict
- **THEN** it moves to the archive, updates canonical specs, and leaves the active inventory consistent

#### Scenario: Archive command reports success without moving
- **WHEN** an archive command returns zero but the active source remains, no unique archive appears, or expected canonical requirements are absent
- **THEN** reconciliation records the batch as failed and stops before the next dependent archive

### Requirement: Complete automation metadata
Every retained active packet SHALL declare strict validation and relevant
verification commands in automation metadata, as SHALL every historical packet
required by repository gates. Reconciliation automation SHALL also strictly
validate all active changes and canonical specs non-interactively.

#### Scenario: Missing automation file
- **WHEN** backlog analysis finds a retained packet without automation metadata
- **THEN** reconciliation adds the appropriate commands or records why the packet is excluded from executable history

### Requirement: Current product documentation
Current-state and roadmap documentation SHALL describe shipped behavior,
unavailable behavior, and the active roadmap consistently. Contract-specific
documentation SHALL remain assigned to the alpha child that changes that
contract.

#### Scenario: Specialized caller wording
- **WHEN** documentation describes how people, scripts, or models use Ladon
- **THEN** it points to the shared caller-independent contract across supported public entrypoints and does not invent a role-specific product surface

#### Scenario: Shipped optional capability
- **WHEN** source and tests show a witness, atlas, or packet capability is present
- **THEN** documentation does not list it as absent or merely planned

### Requirement: Repeatable state-hygiene gate
The existing OpenSpec backlog and status-hygiene tools SHALL fail on new
invalid packets, misleading status drift, stale child references, or unchecked
tasks for verified shipped work after reconciliation.

#### Scenario: Clean reconciled inventory
- **WHEN** the state gate runs after the reconciliation baseline
- **THEN** it reports no unowned active requirement, invalid completed packet, or completed/active metadata drift

### Requirement: Historical preservation
Reconciliation MUST preserve proposal/design/spec evidence and MUST NOT rewrite
history merely to reduce change counts.

#### Scenario: Superseded packet
- **WHEN** a packet is archived as superseded
- **THEN** its historical artifacts and named replacement remain discoverable

#### Scenario: Reconciliation self-archive
- **WHEN** every reconciliation task is complete and each MODIFIED capability's source addition is canonical
- **THEN** the handoff archives reconciliation last, validates canonical specs, and requires the legacy-CLI canonical gate before CLI flag removal integrates
