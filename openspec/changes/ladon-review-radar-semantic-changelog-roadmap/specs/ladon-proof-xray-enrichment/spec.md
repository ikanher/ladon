## ADDED Requirements

### Requirement: Optional x-ray consumer availability
Review Radar SHALL treat separately owned declaration, witness, and future
proof-shape data as optional consumer inputs.

#### Scenario: X-ray backend is disabled
- **WHEN** no elaborated x-ray backend is configured
- **THEN** Review Radar output remains valid and marks x-ray sections as unavailable

#### Scenario: Direct declaration evidence is available
- **WHEN** `ladon-elaborated-declaration-surface` supplies statement, dependency, axiom, sorry, or unsafe rows
- **THEN** Review Radar consumes those rows with their Lean/toolchain provenance and does not define a parallel extractor

#### Scenario: Quoted witness evidence is available
- **WHEN** `ladon-proof-xray-staging` supplies a quoted trust-footprint witness row
- **THEN** Review Radar preserves its backend, authority, source artifact, and theorem-truth nonclaim

#### Scenario: Future proof-shape evidence is available
- **WHEN** `ladon-proof-xray-roadmap` later supplies approved tactic-skeleton or InfoTree evidence
- **THEN** Review Radar consumes the row under its backend/version/source authority and inspection-only nonclaim

### Requirement: X-ray consumer nonclaims
Review Radar SHALL preserve each provider's authority boundary and SHALL NOT
make Ladon the source of theorem truth.

#### Scenario: Tactic skeleton is emitted
- **WHEN** the report includes separately supplied tactic-skeleton or proof-shape rows
- **THEN** it describes them as inspection aids and does not claim that Ladon replayed or validated the proof

#### Scenario: Parser and elaborated rows differ
- **WHEN** parser candidates differ from direct Lean-observed dependency rows
- **THEN** Review Radar keeps both authority classes separate and does not promote parser context into proof-dependency evidence
