# ladon-proof-xray-staging Specification

## Purpose
Accept optional proof-xray witness rows with explicit authority and backend metadata. Keep reporting safe when witnesses are absent; staging does not establish authority beyond the supplied evidence.
## Requirements
### Requirement: Proof-xray witness rows
The system SHALL accept optional proof-xray rows with authority labels and
backend metadata.

#### Scenario: Automation hotspot
- **WHEN** proof-xray evidence reports a long tactic skeleton or automation hotspot
- **THEN** Ladon reports proof-shape pressure with the supplied authority label

#### Scenario: Quoted trust footprint
- **WHEN** a proof-xray witness quotes axiom, sorry, unsafe, or trust-footprint data
- **THEN** the row preserves backend, authority, source-artifact identity, and a nonclaim that Ladon did not infer theorem truth

### Requirement: Absent-safe proof x-ray
The system SHALL skip proof-xray reporting when no witness is supplied.

#### Scenario: Missing witness
- **WHEN** no proof-xray input is supplied
- **THEN** Ladon does not infer proof-shape facts from parser candidates
