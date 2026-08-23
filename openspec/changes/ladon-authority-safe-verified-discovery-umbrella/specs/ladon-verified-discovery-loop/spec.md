## ADDED Requirements

### Requirement: Verified discovery accepts an exact bounded request
The installed discovery workflow SHALL accept a goal, ordered local context, target module/environment, candidate scope, freshness policy, shortlist cap, batch cap, deadline, output bound, memory bound, and explicit execution posture.

#### Scenario: Closed goal with local hypotheses
- **WHEN** a caller supplies typed local hypotheses and a goal in one compiled module
- **THEN** the request preserves their order and identity in the generated check subject and result receipt

#### Scenario: Request exceeds a public bound
- **WHEN** any shortlist, batch, time, memory, context, or output value exceeds its finite supported range
- **THEN** validation rejects the request before database or Lean execution

### Requirement: Shortlisting is bounded, scoped, fresh, and inspectable
The workflow SHALL obtain candidates from the repaired search owner, enforce the selected population and freshness before limiting, and report ranking contributions plus attributable omissions.

#### Scenario: Candidate lies outside scope
- **WHEN** a textually strong declaration is outside the requested module/import population
- **THEN** it is absent from the Lean batch and appears only in an applicable omission diagnostic if the contract exposes excluded populations

### Requirement: Lean verifies candidates in one framed batch operation
The workflow SHALL submit the finite shortlist through a versioned framed Lean worker request under one execution context and SHALL return one independently attributable result for every requested candidate or an explicit batch-level failure affecting them.

#### Scenario: One candidate applies with substitutions
- **WHEN** Lean elaborates a candidate against the goal and instantiates implicit or explicit parameters
- **THEN** the result reports the exact candidate, substitutions, discharged local hypotheses, remaining premises, environment/check references, and accepted application scope

#### Scenario: Plausible candidate is rejected
- **WHEN** a shortlisted declaration cannot elaborate against the exact goal/context
- **THEN** the result retains a bounded normalized Lean rejection reason and never emits an accepted derivation or receipt for that candidate

#### Scenario: Batch terminates early
- **WHEN** timeout, cancellation, protocol failure, output limit, or memory limit interrupts the batch
- **THEN** completed and unassessed candidates remain distinguishable, child processes are reaped, and analysis completeness cannot be complete

### Requirement: Residual premises are exact and ordered
Accepted applications that leave goals SHALL return the worker's ordered residual premises and local-context references without inventing discharge, recursively claiming proofs, or replacing them with generic placeholder text.

#### Scenario: Application leaves two premises
- **WHEN** Lean accepts the application but reports two residual goals
- **THEN** both exact normalized residuals appear in order and the application is partial rather than a closed proof

### Requirement: Scratch compilation is the recorded verification operation
The proposed scratch example SHALL be the exact source checked by the recorded Lean operation or a byte-identical attributable projection with explicit source digest and relationship; its success SHALL not be inferred from a different preflight or candidate result.

#### Scenario: Selected application compiles
- **WHEN** the selected candidate closes the goal under the supplied local context
- **THEN** the workflow returns the checked scratch source identity, successful check reference, zero residuals, and compact evidence receipt

#### Scenario: Displayed scratch source differs
- **WHEN** formatting or rendering changes the source bytes after the check
- **THEN** the displayed derivative receives a distinct digest and cannot inherit compilation authority without a new check

### Requirement: The vertical slice has installed end-to-end acceptance
The repository SHALL contain an installed-wheel fixture with at least one found/explained/compiled candidate and one plausible shortlisted candidate rejected by Lean with its exact failure classification.

#### Scenario: Clean installed workflow runs outside checkout
- **WHEN** the explicit candidate wheel is installed in an isolated supported Python environment
- **THEN** the ordinary command completes the complete discovery loop without `PYTHONPATH`, source-tree imports, network access, or hidden caller-specific wrappers
