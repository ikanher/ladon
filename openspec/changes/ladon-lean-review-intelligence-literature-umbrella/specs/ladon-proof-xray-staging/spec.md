## ADDED Requirements

### Requirement: Optional proof x-ray input
The system SHALL accept optional elaborated proof x-ray rows from a Lean-backed
or external backend and SHALL remain fully functional when no proof x-ray input
is present.

#### Scenario: no proof x-ray backend
- **WHEN** no elaborated proof x-ray backend or witness is supplied
- **THEN** Ladon reports proof x-ray status as unavailable and does not infer proof-shape facts from parser candidates

#### Scenario: proof x-ray rows supplied
- **WHEN** proof x-ray rows are supplied with backend, version, command, source attachment, and confidence metadata
- **THEN** Ladon includes them as optional reviewer context under a proof-xray namespace

### Requirement: Authority labels for proof-shape evidence
The system SHALL label every proof x-ray row as parser-observed,
Lean-elaborated, external-tool-quoted, or unknown and SHALL render that label in
JSON and reviewer-facing outputs.

#### Scenario: tactic skeleton is Lean-elaborated
- **WHEN** a backend supplies a tactic skeleton derived from Lean elaboration or InfoTree data
- **THEN** Ladon reports the skeleton with `Lean-elaborated` authority, backend metadata, and nonclaim text

#### Scenario: dependency row is parser-observed
- **WHEN** a dependency-like row comes only from text or parser reference candidates
- **THEN** Ladon labels it parser-observed and does not present it as an elaborated proof dependency

### Requirement: Proof-shape pressure summaries
The system SHALL summarize proof-shape pressure using available tactic,
goal-state, automation, axiom/sorry/unsafe, and premise/dependency evidence
without deciding whether a proof is correct.

#### Scenario: automation hotspot
- **WHEN** proof x-ray rows show a high concentration of automation tactics, large goal-state changes, or repeated tactic skeletons
- **THEN** Ladon emits a proof-shape review hint with the supporting rows and authority labels

#### Scenario: trust footprint row exists
- **WHEN** proof x-ray rows include axiom, sorry, unsafe, or proof-hole footprint metadata
- **THEN** Ladon reports the footprint as reviewer context and points to proof-surface route audit if a public claim uses the endpoint

### Requirement: Proof x-ray benchmark fixtures
The system SHALL provide synthetic fixtures that prove proof x-ray rows are
authority-labeled, absent-safe, and never promoted to theorem-truth claims.

#### Scenario: parser and elaborated rows disagree
- **WHEN** a fixture has parser-observed candidates that differ from elaborated backend rows
- **THEN** Ladon keeps both evidence classes separate and uses the elaborated row only for proof-xray context
