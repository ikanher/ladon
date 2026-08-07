## ADDED Requirements

### Requirement: Repository-declared representation policy
Ladon SHALL accept optional repository policy that registers representation pairs
with stable IDs, anchored type patterns, directions, named transport declarations,
scale relations, and parameter range classes.

#### Scenario: Valid representation pair
- **WHEN** policy registers normalized and physical state representations
- **THEN** Ladon records the policy source and validates every required identifier, direction, and schema field without hard-coding project names

#### Scenario: Invalid policy
- **WHEN** a representation entry is ambiguous, malformed, or refers to a missing required declaration
- **THEN** Ladon returns an actionable policy diagnostic and does not treat the relation as valid

### Requirement: Lean-checked transport joins
A declared representation transport SHALL be confirmed only when its indexed
elaborated type supports the declared direction and relation.

#### Scenario: Exact conjugacy theorem
- **WHEN** the named normalized-to-physical theorem has the required Lean type
- **THEN** the candidate route links it as Lean-confirmed transport with source, substitutions, and remaining premises

#### Scenario: Policy-only relation
- **WHEN** policy names a semantic relation without a matching elaborated theorem
- **THEN** the relation remains advisory/unresolved and cannot close a premise

### Requirement: Scale-aware candidate diagnostics
Ladon SHALL warn when an available result controls a declared scaled or normalized
object while the goal requests a distinct physical object.

#### Scenario: Normalized bound for physical goal
- **WHEN** the candidate bounds `chi / s` and policy identifies the goal as a bound on `chi`
- **THEN** the route shows the scale factor, required transport, and any unresolved nonzero/positivity premises rather than treating the bounds as equal

### Requirement: Parameter-range classification
Candidates SHALL retain whether their conclusion is fixed-index, finite-window
uniform, unbounded-family uniform, or unknown.

#### Scenario: Hidden horizon growth
- **WHEN** a bound is uniform only up to a retained horizon and its constant depends on that horizon
- **THEN** Ladon surfaces the dependency and does not suggest it as one unbounded-family constant

### Requirement: Policy evidence remains advisory
Representation and scale policy MUST NOT replace exact types, Lean theorem evidence,
or unmatched premises in route cards.

#### Scenario: Review output consumes policy
- **WHEN** a route carries a representation warning
- **THEN** it includes the exact Lean surfaces and labels the policy interpretation separately from theorem authority
