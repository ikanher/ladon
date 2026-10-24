## Purpose

Backward requirement generation and localization against forward contract guarantees. This capability supports bounded prose–formal auditing with explicit evidence and limitations.

## ADDED Requirements

### Requirement: Certified sufficient preconditions
Backward analysis SHALL use admitted transformers that justify their generated preconditions as sufficient for the requested output. It SHALL NOT claim necessity or weakest-precondition status without corresponding checked evidence.

#### Scenario: Converse does not hold
- **WHEN** a rule proves P implies Q but has no certified backward transformer
- **THEN** the analyzer retains an unresolved backward obligation instead of inferring Q implies P

### Requirement: Preserved source goal
Generated obligations SHALL bind the original source interpretation, exact ordered context, object map and rule identities. They SHALL NOT assume the disputed conclusion, missing premise or unfinished parent theorem.

#### Scenario: Circular bridge proposal
- **WHEN** a proposed bridge uses the desired conclusion as a new local assumption
- **THEN** the checker rejects the proposal as support for the original obligation

### Requirement: Route-local discrepancy localization
The analyzer SHALL compare backward requirements with forward contracts and identify unresolved bridges on each explored route. Localization SHALL disclose its route and search scope and SHALL NOT claim a unique or globally minimal cause without evidence.

#### Scenario: Another route succeeds
- **WHEN** one route has a regularity gap and a second route checks successfully
- **THEN** the first gap remains a route finding while the second is reported as endpoint support

### Requirement: Exact obligation checking
Premise supply, representation/domain transport and conclusion transfer SHALL be separately inspectable and checked in the original context. Failed proof search SHALL remain unresolved rather than refuted.

#### Scenario: No bridge term is found
- **WHEN** a bounded search cannot prove a conclusion-transfer obligation
- **THEN** the result records an unresolved bridge and the failed attempts without mathematical-falsity authority

### Requirement: Targeted expansion requests
Missing provider evidence SHALL yield an explicit bounded slice request tied to the unresolved obligation. Generated goals SHALL remain distinguishable from goals observed in original formal source.

#### Scenario: Provider is not yet extracted
- **WHEN** a contract comparison needs the proof of one local premise
- **THEN** the analyzer requests that provider slice and retains the current comparison without claiming whole-proof extraction
