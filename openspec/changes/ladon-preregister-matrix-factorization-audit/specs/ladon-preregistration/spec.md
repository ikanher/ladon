## ADDED Requirements

### Requirement: Matrix-Factorization Ladon Pre-Registration

The matrix-factorization audit SHALL record expected Ladon signals before
running the fresh validation commands.

#### Scenario: pre-registered predictions exist

- GIVEN the matrix-factorization packet is opened
- WHEN the audit runs
- THEN project-level, owner-level, and packet-evidence predictions SHALL
  already be present in the packet design.

#### Scenario: observed results are compared

- GIVEN Ladon reports are generated
- WHEN closeout is performed
- THEN the packet SHALL record whether the observed results matched or
  contradicted the predictions.
