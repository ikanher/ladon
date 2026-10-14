# Spec Delta

## Purpose

Keep source assertions and their exact local contracts in an actionable investigation queue, and distinguish honest stopping from prematurely abandoning available work.

## ADDED Requirements

### Requirement: Bind a selected source population
The controller SHALL initialize a new authored plan over every line of the selected UTF-8 text, bind it by digest, and expose unexamined units and inventory attribution. Existing plans SHALL not be overwritten by initialization.

#### Scenario: A broad reading has only a few comparisons
- **WHEN** most source units are still pending despite selected endpoints being reviewed
- **THEN** the next batch requires source inventory and finalization remains unavailable before the deadline

#### Scenario: Input or scope binding is stale
- **WHEN** the source digest, quoted span or unit coverage fails validation
- **THEN** the command rejects the plan without a completed-investigation result

### Requirement: Require exact local contract records
A compared claim SHALL bind an unchanged source quote and formal statement to source spans and record objects, assumptions, domains, quantifiers, conclusion, dependencies and needed implication for both interpretations. Statement and method judgments SHALL remain attributed and separate.

#### Scenario: A claim has only a theorem summary
- **WHEN** a captured claim lacks its exact contract or the formal counterpart
- **THEN** it remains actionable, with the missing operation named, regardless of endpoint success

#### Scenario: Source correspondence remains uncertain
- **WHEN** both source records are bound but the interpreted implication remains unresolved
- **THEN** the queue retains the unresolved obligation rather than treating a recorded review as completion

### Requirement: Continue available work before stopping
Before its recorded deadline, finish SHALL return a nonzero status and a next batch whenever an inventory, contract, comparison or unresolved follow-up remains actionable. Genuine blockers SHALL have a kind, evidence, next action and unblock condition. Exhausted budgets SHALL permit only an explicitly incomplete conclusion.

#### Scenario: Fifteen minutes of a ninety-minute budget have elapsed
- **WHEN** actionable claims or unexamined units remain
- **THEN** finish rejects early closure and emits the next useful work

#### Scenario: Deadline or concrete blocker stops work
- **WHEN** the deadline is exhausted or every remaining obligation has an evidenced blocker
- **THEN** finish reports incomplete-budget or incomplete-blocked and preserves all residuals

### Requirement: Keep validation separate from mathematics
The controller SHALL describe its results as source-binding and workflow checks, not mathematical truth or semantic inventory completeness. It SHALL perform no Lean build, network call, model request or automatic semantic comparison.

#### Scenario: A bound review is mathematically wrong
- **WHEN** an authored comparison has valid fields but an incorrect interpretation
- **THEN** structural validation does not certify that interpretation or label the exposition correct

### Requirement: Validate bounded local inputs
Commands SHALL reject malformed plans, duplicate identifiers, invalid timestamps/budgets, invalid ranges, missing records and paths outside the explicitly allowed source root. Reads and queue output SHALL be bounded.

#### Scenario: A plan escapes its source root
- **WHEN** a source reference traverses outside the root or follows an escaping symlink
- **THEN** validation fails without reading the outside content

### Requirement: Preserve experiments and clean restart inputs
Failed and earlier scored records SHALL remain immutable historical evidence. The new restart workspace SHALL contain only primary inputs and neutral procedure/operational guidance, excluding known diagnoses and earlier runs. No implementation acceptance SHALL imply successful research-paper detection.

#### Scenario: A new restart follows workflow upgrades
- **WHEN** the upgraded procedure is delivered
- **THEN** earlier findings remain intact and the fresh handoff has no fault location, mathematical diagnosis or selected passage
