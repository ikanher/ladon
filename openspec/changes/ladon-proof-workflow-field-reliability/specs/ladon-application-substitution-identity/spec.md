## Purpose
Represent instantiated declaration parameters without confusing repeated display names and preserve each candidate's independent evidence outcome.

## ADDED Requirements

### Requirement: Substitutions use scoped parameter identity
Application evidence SHALL distinguish declaration parameters by stable scoped identity even when their display names repeat. Contradictory bindings for the same identity SHALL still fail validation.

#### Scenario: Transitivity parameters repeat names
- **WHEN** an application of a transitivity lemma leaves an unknown intermediate term
- **THEN** evidence preserves distinct parameter bindings and exact residual contexts rather than failing because displayed binder names collide

### Requirement: Candidate failures preserve independent results
Discovery SHALL retain validated observations for independent candidates while reporting another candidate's evidence failure as unassessed operational evidence.

#### Scenario: Mixed batch
- **WHEN** one candidate has invalid evidence and another has an independently valid application
- **THEN** discovery preserves the valid application and exposes the failed candidate without claiming its acceptance

### Requirement: Discovery exposes limits and acceptance scope
Compact discovery SHALL expose the requested candidate limit and distinguish closed accepted applications from applications with residual obligations.

#### Scenario: Accepted and residual candidates
- **WHEN** a discovery batch has one accepted candidate, one residual application and one rejection
- **THEN** the summary identifies those three outcomes distinctly and reports the requested candidate bound
