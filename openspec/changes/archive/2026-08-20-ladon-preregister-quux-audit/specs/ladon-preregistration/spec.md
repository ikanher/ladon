## ADDED Requirements

### Requirement: Quux Ladon Pre-Registration

The Quux audit SHALL record expected Ladon signals before running the fresh
validation commands.

#### Scenario: pre-registered predictions exist

- GIVEN the Quux packet is opened
- WHEN the audit runs
- THEN project-level and owner-level predictions SHALL already be present in
  the packet design.

#### Scenario: observed results are compared

- GIVEN Ladon reports are generated
- WHEN closeout is performed
- THEN the packet SHALL record whether the observed results matched or
  contradicted the predictions.
