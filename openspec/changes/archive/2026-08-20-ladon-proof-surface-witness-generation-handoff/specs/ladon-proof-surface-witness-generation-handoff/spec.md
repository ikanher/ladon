## ADDED Requirements

### Requirement: Existing proof-surface audit reuse
The system SHALL reuse the existing proof-surface route audit for trust
diagnostics and SHALL NOT create a duplicate proof authority mechanism.

#### Scenario: Route completeness is reported
- **WHEN** a claim route has proof-surface metadata
- **THEN** Ladon reports completeness fields derived from existing endpoint, gate, axiom, and attachment predicates

### Requirement: Verifier metadata preservation
The system SHALL preserve build, source pin, no-drift, axiom audit, replay
boundary, command, and tool-version metadata from proof-surface handoff rows.

#### Scenario: Axiom audit handoff metadata
- **WHEN** an axiom audit row carries verifier commands or replay boundary metadata
- **THEN** Ladon preserves that metadata in route output
