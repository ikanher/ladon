## ADDED Requirements

### Requirement: Lean-backed candidate difference
Given an elaborated goal, local context, and candidate declaration, Ladon SHALL report
binder substitutions, synthesized implicits, premises discharged by local hypotheses,
and exact unmatched premises.

#### Scenario: Candidate conclusion matches with row guard
- **WHEN** a retained-row theorem matches the goal conclusion but requires a row or horizon inequality absent from context
- **THEN** the difference identifies that exact residual premise instead of reporting only that application failed

#### Scenario: Candidate is stronger than goal
- **WHEN** the instantiated candidate conclusion Lean-converts to a proposition stronger than or exactly satisfying the goal
- **THEN** the row records the supported relation and preserves any premises still required

### Requirement: Evidence-backed mismatch classification
Residual premises SHALL retain their elaborated types and MAY receive stable
classifications only when structural or validated policy evidence supports them.

#### Scenario: Measurability strength mismatch
- **WHEN** the residual route requires conversion between `StronglyMeasurable` and `AEStronglyMeasurable`
- **THEN** the response names both exact propositions, the direction, and any required measure-side conditions

#### Scenario: Unrecognized difference
- **WHEN** no supported classifier applies
- **THEN** Ladon emits `unclassified-premise` with the exact type rather than guessing a semantic label

### Requirement: Premise discharge search
For every unmatched premise, Ladon SHALL be able to query in-scope declarations that
may discharge it and retain their own match, scope, and freshness evidence.

#### Scenario: Lower-level declaration removes guard
- **WHEN** an all-row lower-level theorem proves a residual premise needed by a restricted wrapper
- **THEN** the route card links the exact declaration and shows the remaining obligations after composing that step

### Requirement: Side-condition-complete adapter suggestions
Adapter suggestions MUST name exact declarations, input/output shapes, direction,
and every side condition known to the registered route, and MUST remain advisory
until Lean confirms an application probe.

#### Scenario: Integrability adapter
- **WHEN** a candidate could use a registered integrability transport, monotonicity, finite-sum, almost-everywhere, or arithmetic-normalization route
- **THEN** Ladon shows the adapter declaration and unresolved side conditions without saying the proof compiles

#### Scenario: Unsupported text resemblance
- **WHEN** two propositions are lexically similar but no Lean or registered adapter route connects them
- **THEN** Ladon does not emit a confirmed adapter suggestion

### Requirement: Durable proof-route cards
Accepted and rejected routes SHALL have deterministic machine-readable cards carrying
goal/candidate fingerprints, substitutions, premise states, adapters, source owners,
scope/freshness, probe status, and explicit nonclaims.

#### Scenario: Rejected route persists
- **WHEN** a probe or premise check rejects a route
- **THEN** the card records the exact failure stage and can be consumed by later search and review output
