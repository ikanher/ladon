## ADDED Requirements

### Requirement: Optional x-ray enrichment
The system SHALL treat Proof X-Ray data as optional enrichment for Review Radar
and semantic changelog outputs.

#### Scenario: X-ray backend is disabled
- **WHEN** no elaborated x-ray backend is configured
- **THEN** Review Radar and semantic changelog outputs remain valid and mark x-ray sections as unavailable

#### Scenario: X-ray backend is enabled
- **WHEN** an elaborated backend supplies theorem surface, tactic skeleton, dependency, axiom, sorry, unsafe, or proof-shape metadata
- **THEN** the report includes the metadata under a clearly labeled x-ray namespace with backend, tool version, source hash, and confidence fields

### Requirement: X-ray authority labels
The system SHALL label every x-ray field by extraction authority and SHALL NOT
merge parser-level observations with Lean-elaborated facts.

#### Scenario: Parser candidate and elaborated dependency differ
- **WHEN** parser-level reference candidates differ from elaborated dependency metadata
- **THEN** the report keeps both rows separately and labels the parser row as review context rather than proof dependency evidence

#### Scenario: Axiom footprint is reported
- **WHEN** the x-ray backend reports axiom, sorry, or unsafe footprint metadata
- **THEN** the report identifies the backend and source artifact used for that footprint

### Requirement: X-ray nonclaims
The system SHALL state that x-ray enrichment explains proof shape and authority
metadata without making Ladon the source of theorem truth.

#### Scenario: Tactic skeleton is emitted
- **WHEN** the report includes tactic skeleton or proof-shape rows
- **THEN** it describes them as inspection aids and does not claim that Ladon replayed or validated the proof

#### Scenario: Dependency metadata is emitted
- **WHEN** the report includes dependency names from an elaborated backend
- **THEN** it marks them as backend-supplied dependency metadata and includes the backend identity
