## Purpose

Evidence-bound application probes that distinguish mathematical contracts. This capability supports bounded prose–formal auditing with explicit evidence and limitations.

## ADDED Requirements

### Requirement: Feature-bound probe generation
A probe SHALL identify the compared contracts, affected feature, exact context, object map, template version and checker. The admitted families SHALL cover regularity, constant uniformity, witness dependence, domains and inequality direction.

#### Scenario: Uniformity probe
- **WHEN** contracts differ in whether a constant can be chosen before a parameter
- **THEN** the generated goal preserves that quantifier order and does not replace it with a pointwise application

#### Scenario: Restricted-domain application
- **WHEN** a source-bound pair compares `∀ x : Nat, P x` with `∀ x : Nat, x ≤ 0 → P x` under the exact restricted-domain-v2 profile
- **THEN** the planner preserves both original readings, emits an open directional implication or counterexample goal, and leaves semantic separation unresolved until checked evidence is accepted

#### Scenario: Nat zero-bound inequality reversal
- **WHEN** a source-bound pair compares `∀ x : Nat, x ≤ 0` with `∀ x : Nat, 0 ≤ x` under the exact inequality-direction-v2 profile
- **THEN** the planner preserves both readings, recognizes only the built-in Nat zero-bound operand reversal under the exact `object:nat-order` / `domain:Nat` / `scale:none` / `representation:original` context, emits open directional implication or counterexample goals, and leaves semantic separation unresolved until checked evidence is accepted

### Requirement: Semantic separation evidence
Semantic separation SHALL require checked evidence for the exact relevant implication or its counterexample. Application rejection, timeout or failed term search alone SHALL NOT establish non-implication.

#### Scenario: One side fails elaboration
- **WHEN** a supplied application term checks on one side and is rejected on the other
- **THEN** the result records an application difference and unresolved semantic separation unless further evidence establishes it

#### Scenario: Probe proof fails or its deadline expires
- **WHEN** Lean rejects a generated probe proof during elaboration or tactic search, or the shared deadline expires
- **THEN** the probe remains unresolved or incomplete, and the result does not report semantic non-implication or mathematical falsity

### Requirement: Scoped probe agreement
Agreement on a finite family SHALL report only agreement on that family unless a checked separating-family theorem covers the exact object class, responses and probes.

#### Scenario: Incomplete family agrees
- **WHEN** two unequal calibration objects agree on every selected probe
- **THEN** the system does not report equivalence without a valid separation certificate

### Requirement: Exact replay and bounds
Probe results SHALL bind template, subject, environment, assumptions, checker identity and bounded execution evidence. Every attempted probe SHALL remain reportable, including unsupported and budget-exhausted attempts.

#### Scenario: Cached result has another context
- **WHEN** a probe result is offered for a goal with changed assumptions
- **THEN** it is rejected as stale or mismatched rather than reused as support

#### Scenario: Exact cached goal receipt from trusted local store
- **WHEN** a prior checked result is supplied for reuse and fresh bounded preparation regenerates the identical plan and goals under the same absolute deadline
- **THEN** only hash-verified accepted receipts with the exact same goal and proof-term digest are reused, each reused goal is identified in the result, and all changed assumptions, sources, environments, checker identities, template revisions, limits, or deadlines reject reuse

#### Scenario: Cache origin trust boundary
- **WHEN** cached evidence is read from the repository-local Ladon evidence store
- **THEN** content addressing detects mutation and binding detects context/goal/term mismatch, while the caller is responsible for using trusted Ladon-generated cache data; this mechanism does not authenticate against a malicious writer with access to that local store

#### Scenario: Cached evidence is transplanted between goals
- **WHEN** an accepted content-addressed receipt reference is attached to another generated goal, even when both goals use the same proof term
- **THEN** the receipt's plan, goal ID, goal digest and goal text binding fails, so the result remains unresolved and grants no cached checker authority

#### Scenario: Cached result after deadline expiry
- **WHEN** the shared absolute deadline has expired before reuse begins
- **THEN** the result is incomplete with a timeout and no cached checker authority is retained

### Requirement: Independent review and controls
Probe review packets SHALL preserve original subjects and checker evidence while excluding proposed verdicts. Evaluation SHALL include valid transports and harmless proof-route differences as controls.

#### Scenario: Valid representation bridge
- **WHEN** a checked subset-to-subtype translation changes the statement's presentation
- **THEN** the probe workflow recognizes the checked bridge without accusing the original statement

#### Scenario: Reviewer packet retains attempts without candidate verdict
- **WHEN** reviewer export receives ordered result envelopes for the same inspected source-bound probe, including failed, unsupported, stopped and later attempts
- **THEN** it preserves every attempt in input order with original source readings and available raw checker receipts, and emits no proposed semantic verdict or authority label in reviewer input
- **AND** it reports checks completed only when every generated goal has one exact matching row, a completed execution receipt, a supported raw receipt with accepted replay/trust state, and a receipt term digest matching the supplied term
- **AND** it labels incomplete goal coverage or inconsistent/unavailable checker evidence as partial or unverified execution evidence
