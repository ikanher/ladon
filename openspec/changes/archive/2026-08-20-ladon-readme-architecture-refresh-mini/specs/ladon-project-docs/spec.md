## ADDED Requirements

### Requirement: Project Docs Match Implemented Surfaces

The project README and architecture guide SHALL describe the current supported
Ladon surfaces without claiming unsupported prototype features.

#### Scenario: README documents current backends

- GIVEN a user reads `README.md`
- WHEN they choose a Ladon run mode
- THEN the README SHALL show both the text module-DAG backend and Lean root
  declaration graph backend.

#### Scenario: architecture guide marks rebuilt surfaces as supported

- GIVEN a contributor reads `docs/ARCHITECTURE.md`
- WHEN they inspect current supported modules
- THEN Lean extraction, declaration graph analysis, and pipeline timing SHALL be
  listed as implemented.

#### Scenario: limitations remain explicit

- GIVEN a user reads the docs
- WHEN they look for packet review, witness audit, or export freshness checks
- THEN the docs SHALL state those surfaces are not yet rebuilt.
