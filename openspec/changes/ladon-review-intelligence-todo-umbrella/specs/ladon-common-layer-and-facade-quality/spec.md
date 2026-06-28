## ADDED Requirements

### Requirement: Common-Layer and Facade Quality Triage

Ladon SHALL distinguish common-layer candidates, intentional facade modules,
and mixed facade/implementation modules using generic source-shape and
policy-group evidence.

#### Scenario: multi-group common dependency is ranked

- **WHEN** multiple configured source groups import the same target
- **THEN** Ladon SHALL report a common-layer candidate with importing groups,
  importer count, dependency scope, and confidence.

#### Scenario: pure facade is separated from implementation coupling

- **WHEN** a module is a pure public barrel or generated aggregation module
- **THEN** Ladon SHALL classify it separately from ordinary implementation
  fan-out.

#### Scenario: mixed facade receives review pressure

- **WHEN** a module combines broad imports with local declarations
- **THEN** Ladon SHALL identify the mixed facade shape so reviewers can inspect
  whether aggregation and implementation should be split.
