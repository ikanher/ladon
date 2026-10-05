## ADDED Requirements

### Requirement: Disclosed generation records identify their source
Following [Responsible Release of AI-Generated Mathematics](https://agmai.org/general-sep29/) (2026-09-29), §2.B Step I.3 and I.5, Ladon SHALL import supplied model/provider/version IDs, prompts or disclosure statuses, input/output references, concise process summaries, tool events, runtime, and cost estimates. Each record SHALL name its supplier, capture method, result/problem/attempt IDs, and observed versus reported fields. Source mapping SHALL remain in `../../sources.md`.

#### Scenario: Cost and model details are only producer-reported
- **WHEN** the producer supplies a model name and an estimated compute cost without execution receipts
- **THEN** the record preserves those values as reported with currency and estimation basis and does not present them as independently measured

### Requirement: Problems and attempts have separate inventories
The system SHALL distinguish stable problem identities, attempts, batches, problem-selection rationale, AI involvement, and result links. Outcomes SHALL distinguish success, failure, timeout, abandonment, and unassessed states, with explicit success criteria and evidence. Checker acceptance SHALL NOT be inferred from a producer's success label. Claims of comparable problem difficulty SHALL remain attributed rationale.

#### Scenario: Several attempts target the same problem
- **WHEN** three attempts address one problem and only the final attempt is reported successful
- **THEN** the ledger reports one problem and three attempts with separate outcomes and does not count three distinct problems

### Requirement: Population coverage governs aggregate rates
Each inventory SHALL declare its capture boundary, time interval or batch, inclusion/exclusion policy, and complete, partial, or unknown coverage. Rates SHALL state their population and denominator. Partial or unknown capture SHALL NOT produce a global success rate; any observed-subset rate SHALL be explicitly labeled and retain missingness. A complete inventory claim SHALL retain its source rather than imply access to unobserved lab activity.

#### Scenario: Only published successes were imported
- **WHEN** an import contains successful results but the number of unsuccessful problems is unknown
- **THEN** the unsuccessful population and global success rate remain unknown instead of being reported as zero failures or complete success

### Requirement: Disclosure choices survive inspection and export
Prompt, output, and event attachments SHALL support supplied, redacted, unavailable, and not-collected statuses with reasons. Exports SHALL include only explicitly allowed content, omit content-derived identifiers that would expose redacted secrets, and record disclosure limitations. Missing prompts SHALL NOT be reconstructed. Supplied process summaries SHALL NOT claim access to hidden internal reasoning.

#### Scenario: A prompt attachment contains material excluded from release
- **WHEN** the producer marks that attachment redacted and exports an allowlisted bundle
- **THEN** no excluded prompt bytes or reversible content-derived secret identifiers appear and the bundle records the redaction without inventing a replacement prompt

### Requirement: Initial and edited artifacts remain distinguishable
The system SHALL preserve distinct revision identities and explicit transformation links for original model outputs, edited proofs, and reviewed exposition. Editing SHALL NOT overwrite the historical input/output record or imply that a model generated the final human-edited text.

#### Scenario: A mathematician rewrites an initial proof
- **WHEN** the revised exposition is attached to the same mathematical result
- **THEN** the bundle can distinguish original output, edited version, editor attribution, and review status while honoring disclosure permissions
