## ADDED Requirements

### Requirement: Calibration Regression Roadmap

Ladon SHALL maintain a spec-backed roadmap for turning pre-registered audit
observations into durable calibration checks.

#### Scenario: child packets are enumerated

- GIVEN the umbrella packet is opened
- WHEN maintainers inspect the design
- THEN the packet SHALL list calibration children in execution order.

#### Scenario: no brittle full-report snapshots

- GIVEN calibration checks are implemented
- WHEN they compare reports
- THEN they SHALL use stable predicates rather than exact complete JSON
  snapshots.
