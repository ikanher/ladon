## Purpose

Bounded countermodel checking, minimization and evidence-supported abstraction refinement. This capability supports bounded prose–formal auditing with explicit evidence and limitations.

## ADDED Requirements

### Requirement: Exact witness admission
A countermodel SHALL satisfy every premise and falsify the conclusion of its exact declared interpretation under a supported checker. Candidate enumeration and arithmetic SHALL be explicitly bounded.

#### Scenario: A premise is false
- **WHEN** a candidate falsifies the conclusion but violates one assumption
- **THEN** the outcome is outside-assumptions rather than a counterexample

### Requirement: Original-context lifting
An abstract countermodel SHALL NOT establish falsity of an original mathematical statement without a checked realization satisfying its full constraints. Unsupported lifting SHALL remain a named unresolved obligation.

#### Scenario: Scalar assignment lacks a function realization
- **WHEN** a rational countermodel exists but no realization in the original function space has been checked
- **THEN** the finding remains an abstract countermodel and does not refute the original theorem

#### Scenario: Source changes the meaning of a generated rational expression
- **WHEN** source-defined notation or instances make the elaborated goal differ from the checked profile's canonical proposition
- **THEN** the checker refuses a positive lifting or spuriousness result even if Lean accepts a proof of that different proposition

#### Scenario: A fresh formal realization succeeds
- **WHEN** fresh source, canonical goal, complete mapping, realization and trusted replay checks all succeed for the selected formal interpretation
- **THEN** the result may report a lifted counterexample to that formal claim while retaining the original witness and leaving prose fidelity and original prose falsity unestablished

### Requirement: Evidence-supported spuriousness
A countermodel SHALL be labeled spurious only when evidence establishes incompatibility with an original constraint or interpretation. Failure to find a realization SHALL NOT establish spuriousness.

#### Scenario: Realization search times out
- **WHEN** lifting search ends without a witness or incompatibility proof
- **THEN** the model remains unresolved rather than spurious

### Requirement: Immutable justified refinement
Each refinement SHALL preserve parent contracts, witnesses and first findings and identify evidence for every added constraint. Strengthening the manuscript claim SHALL be recorded as a separate proposed repair, not support for the original claim.

#### Scenario: Missing assumption is proposed
- **WHEN** an auditor adds an assumption absent from the original passage to remove a countermodel
- **THEN** the new branch is labeled a repair and the original discrepancy remains visible

### Requirement: Bounded rational branch checks
A rational branch checker SHALL accept only predicates in the existing bounded rational AST, append each cumulative branch predicate as a premise to a copied base goal, and check only the supplied assignment. Its result SHALL bind the exact branch, base goal, derived goal, assignment representation and checker identity. Reverification SHALL recompute the result against the current branch and source spans. A source citation SHALL NOT certify formula fidelity, branch parent labels SHALL NOT certify authenticated lineage, and no outcome SHALL refute the original prose or proposed repair.

#### Scenario: A branch predicate is outside the supported language
- **WHEN** a refinement contains free text, arbitrary JSON or an AST outside the rational predicate grammar
- **THEN** the check is rejected rather than interpreted heuristically

#### Scenario: A branch check is replayed after its context changes
- **WHEN** the branch, base goal, assignment or cited source changes
- **THEN** verification rejects the saved result or recomputes a distinct identity for the new request

#### Scenario: A source-cited predicate has a passing assignment
- **WHEN** the encoded rational predicates and conclusion hold for the supplied assignment
- **THEN** the result reports only that assignment's status for the derived encoded goal and keeps source formula fidelity unverified

### Requirement: Scoped minimization
Minimization SHALL identify the reduction relation, decreasing measure, checked reductions and completed search scope. It SHALL claim only the minimality supported by that scope.

#### Scenario: Reduction budget expires
- **WHEN** a smaller countermodel is found before every allowed reduction is checked
- **THEN** the output reports the smaller witness without claiming irreducibility or global minimality

### Requirement: Finite loop accounting
Refinement SHALL share the original deadline and candidate, reduction and round limits. Finite survival SHALL NOT establish universal validity, and changed contracts SHALL invalidate dependent checks.

#### Scenario: No witness in enumerated family
- **WHEN** all allowed candidates survive and the search ends
- **THEN** the result reports survived-declared-scope with its exact family and no universal support claim

### Requirement: Public refinement evidence workflow
The public refinement command SHALL preserve the exact original finding, goal,
witness and checks while invoking the source-owned lift checker before branch
checks under one deadline. Source-cited constraints and proposed repairs SHALL
produce separate branches. A resource stop SHALL preserve partial evidence and
SHALL NOT initiate subsequent branch checks or an automatic retry.

#### Scenario: A checked spurious witness motivates a refinement
- **WHEN** fresh Lean checking establishes incompatibility with the selected formal interpretation
- **THEN** the output retains the original rational counterexample and saved lift evidence alongside separate source-cited and repair branch checks, without certifying prose fidelity or universal truth

### Requirement: Historical inspection and report preservation
Saved refinement inspection SHALL recompute rational checks and current source
bindings while treating imported native lift evidence as unverified historical
claims. Reports SHALL retain original findings, branch findings and pending work
alongside the supplement. Finding-ID association SHALL be explicit and SHALL NOT
certify semantic correspondence or resolve review obligations.

#### Scenario: Saved lift evidence is replaced and rehashed
- **WHEN** a caller supplies self-consistent historical JSON with edited native evidence
- **THEN** inspection either rejects its inconsistent bindings or preserves it with no fresh lift authority, no Lean replay and no source-fidelity claim

#### Scenario: A supplement names an absent finding
- **WHEN** the supplied original finding ID has no matching report finding
- **THEN** report aggregation rejects the supplement instead of silently creating or replacing a finding
