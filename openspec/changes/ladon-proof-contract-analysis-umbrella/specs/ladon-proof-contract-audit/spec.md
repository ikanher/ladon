## Purpose

Integrated contract-audit workflow and truthful evidence projection across the child capabilities. This capability supports bounded prose–formal auditing with explicit evidence and limitations.

## ADDED Requirements

### Requirement: Resumable contract audit
The system SHALL expose a bounded opt-in workflow for contract production, propagation, obligation generation, probing, refinement and inspection. Each stage SHALL retain immutable input identities, results and unresolved work and SHALL remain inspectable when a later stage is unsupported.

#### Scenario: A formal feature is unsupported
- **WHEN** a source contract is captured but its formal counterpart cannot be fully summarized
- **THEN** inspection preserves the source observation and queues the unsupported feature without claiming a completed correspondence

### Requirement: Independent result dimensions
Audit findings SHALL separately report source fidelity, extraction completeness, route support, method correspondence, checked mathematical falsity and explored population. A matching endpoint SHALL NOT erase a discrepancy in the described route.

#### Scenario: An alternative proof closes the endpoint
- **WHEN** a checked alternate route establishes the endpoint while the prose route lacks a premise
- **THEN** the endpoint support and the unresolved prose-route premise remain separate findings

### Requirement: Persistent finding projection
Reviewed contract findings SHALL survive status, inspection, aggregation and final receipts with original evidence and review history, including when no main claim entry exists. Historical receipt validation SHALL preserve its original semantics.

#### Scenario: Observation-only discrepancy
- **WHEN** a contract discrepancy is independently reviewed in a supplementary observation plan
- **THEN** the final report retains the discrepancy, originating plan, source location and authority without promoting it to theorem falsity

### Requirement: Shared bounds and resource stops
All audit stages SHALL share the declared deadline and finite work limits. Memory exhaustion SHALL use the ordinary configured process limit, stop dependent progress and instruct the caller to report to the user; retries SHALL NOT silently increase limits or reset the clock.

#### Scenario: Probe worker exceeds its cap
- **WHEN** a probe worker exceeds the default 12 GiB RSS cap
- **THEN** the audit retains completed evidence and reports the configured cap and available measured peak without launching an automatic higher-cap retry

### Requirement: Portable additive integration
The workflow SHALL operate without a Quux checkout or mandatory model service and SHALL preserve existing native artifacts, structural queries and historical runs. New semantic kinds SHALL be explicitly supported or rejected by each consumer.

#### Scenario: Old consumer receives a contract artifact
- **WHEN** a reader does not implement the new contract kind
- **THEN** it returns an unsupported-kind result rather than accepting or projecting it as checked evidence

### Requirement: Qualified benefit gate
The system SHALL report implementation readiness separately from supplied-contract correctness, source-production accuracy and unfamiliar-source detection benefit. A failed or nonblind evaluation SHALL NOT satisfy the discovery gate.

#### Scenario: Development replay succeeds
- **WHEN** known-answer examples pass but fresh discovery does not meet the frozen promotion rule
- **THEN** the report credits only development correctness and leaves detection benefit unestablished
