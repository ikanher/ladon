## ADDED Requirements

### Requirement: Proof X-Ray Roadmap

Ladon SHALL define a later elaborated-backend roadmap for proof-shape evidence
while preserving the distinction between parser candidates and Lean-owned proof
artifacts.

#### Scenario: tactic skeleton is quoted as extracted evidence

- **WHEN** an elaborated backend supplies tactic or info-tree structure
- **THEN** Ladon SHALL report tactic skeleton evidence with backend and version
  metadata.

#### Scenario: axiom and sorry footprint has authority labels

- **WHEN** Lean-backed extraction supplies axiom, sorry, unsafe, or trust
  footprint data
- **THEN** Ladon SHALL label the extraction source and SHALL NOT infer theorem
  truth from the footprint row.

#### Scenario: parser reference is not promoted

- **WHEN** parser-level reference candidates and elaborated dependencies both
  appear in reports
- **THEN** Ladon SHALL keep them in distinct fields with distinct confidence and
  authority labels.
