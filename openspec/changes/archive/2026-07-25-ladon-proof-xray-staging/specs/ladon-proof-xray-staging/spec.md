## ADDED Requirements

### Requirement: Proof-xray witness rows
The system SHALL accept optional proof-xray rows with authority labels and
backend metadata.

#### Scenario: Automation hotspot
- **WHEN** proof-xray evidence reports a long tactic skeleton or automation hotspot
- **THEN** Ladon reports proof-shape pressure with the supplied authority label

### Requirement: Absent-safe proof x-ray
The system SHALL skip proof-xray reporting when no witness is supplied.

#### Scenario: Missing witness
- **WHEN** no proof-xray input is supplied
- **THEN** Ladon does not infer proof-shape facts from parser candidates
