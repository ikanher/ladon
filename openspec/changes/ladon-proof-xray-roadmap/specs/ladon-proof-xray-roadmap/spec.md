## ADDED Requirements

### Requirement: Proof X-Ray Evidence Contract

Ladon SHALL define future proof-shape evidence rows with explicit authority
labels and nonclaims.

#### Scenario: tactic skeleton has backend metadata

- **WHEN** tactic skeleton evidence is reported
- **THEN** it SHALL include backend, version, and confidence metadata.

#### Scenario: trust footprint is labeled

- **WHEN** axiom, sorry, unsafe, or trust-footprint data is reported
- **THEN** Ladon SHALL label the extraction source and SHALL NOT infer theorem
  truth from the row.

#### Scenario: parser references stay separate

- **WHEN** parser references and elaborated dependencies both appear
- **THEN** they SHALL use distinct fields and confidence labels.
