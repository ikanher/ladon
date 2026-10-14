# Spec Delta

## Purpose

Represent precise, attributed interpretations of original mathematical prose so
that local reasoning can be compared with formal evidence without erasing ambiguity.

## ADDED Requirements

### Requirement: Immutable source-bound interpretations
An interpretation SHALL bind the original source bytes, exact span and quotation, surrounding context references, producer, and interpretation identity. Revisions SHALL create new interpretations without overwriting the original claim or silently inheriting its reviews.

#### Scenario: Repair changes a hypothesis
- **WHEN** an author adds an assumption to make a disputed claim provable
- **THEN** the revised interpretation has a distinct identity and the original obligation remains available with its original status

### Requirement: Structured binder scope and dependency permissions
The admitted structured fragment SHALL preserve binder identity, type or domain, quantifier order, hypothesis scope, and permitted witness or constant dependencies. It SHALL reject dangling or captured references and distinguish faithful renaming from a change in dependency permissions.

#### Scenario: Pointwise witness becomes uniform
- **WHEN** a statement permitting a separate witness for each parameter is compared with one common witness for all parameters
- **THEN** the forms remain distinct and the stronger dependency requirement becomes an explicit obligation rather than an accepted textual normalization

#### Scenario: Harmless bound-variable renaming
- **WHEN** bound display names change while scoped references and permitted dependencies remain consistent
- **THEN** the structural comparison does not report a mathematical discrepancy solely from those names

### Requirement: Alternative meanings remain separately assessable
An ambiguous passage SHALL support multiple attributed interpretations with independently scoped evidence and a separate fidelity assessment. Checking one interpretation SHALL NOT select it as the source's intended meaning or transfer its verdict to another interpretation.

#### Scenario: Informal neighborhood wording
- **WHEN** both pointwise and uniform readings are retained and only the uniform reading is refuted
- **THEN** the result names that reading and preserves the qualification instead of declaring the unqualified sentence false

### Requirement: Explicit elaboration and unsupported boundaries
The system SHALL distinguish authored prose structure, Lean elaboration, and review of source fidelity. Unsupported mathematical syntax SHALL remain opaque or unresolved with a limitation; successful elaboration SHALL establish only the recorded typed interpretation.

#### Scenario: Analytic notation exceeds the structured fragment
- **WHEN** an interpretation includes an unsupported analytic operator
- **THEN** the system preserves the original expression and reports the unsupported boundary without fabricating a complete semantic parse

### Requirement: Native interpretation identity and validation
New interpretations SHALL use an explicitly supported closed native ProofIR payload with canonical identity, bounded validation, and exact source and statement references. Unknown payload fields, invalid reference scopes, and modified bound content SHALL fail validation or invalidate dependent evidence.

#### Scenario: Source wording changes after review
- **WHEN** the bound source quotation changes but the stored review is reused
- **THEN** the interpretation or review is reported stale and cannot retain current checked correspondence

### Requirement: Structured and checked propositions agree
Checked obligations SHALL derive from the exact structured interpretation through a scope-preserving supported translation. A separately supplied Lean presentation SHALL be checked against that translated subject before its results can support the interpretation. Unsupported translation SHALL remain incomplete.

#### Scenario: Displayed quantifiers disagree with supplied Lean goal
- **WHEN** the structured interpretation requires one common witness but the supplied Lean expression permits a separate witness for each parameter
- **THEN** acceptance of the weaker Lean goal cannot be attached as a check of the structured interpretation
