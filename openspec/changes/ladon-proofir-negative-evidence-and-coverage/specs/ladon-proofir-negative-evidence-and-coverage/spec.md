## ADDED Requirements

### Requirement: Coverage distinguishes absence from unavailability
The system SHALL report configuration, availability, inspected population, matched population, state, and reasons separately for catalog, surface, claim, attachment, replay, DAG, witness, and lineage evidence.

#### Scenario: Unconfigured ProofIR
- **WHEN** no ProofIR manifest is configured
- **THEN** evidence is `not-configured` rather than absent or complete-empty

#### Scenario: Configured inspected population has no theorem surface
- **WHEN** supported surfaces were inspected but none explicitly identify the theorem
- **THEN** surface evidence is observed-absent for that selector with the inspected population count

#### Scenario: Lineage unavailable
- **WHEN** no compatible lineage generation exists
- **THEN** lineage is unavailable and no absence claim is made about Lean dependencies

### Requirement: Negative evidence reasons remain independent
The system SHALL preserve stale, ambiguous, malformed, unsupported, failed, unmatched, missing, and context-only reasons independently rather than collapsing them to one unavailable state.

#### Scenario: Stale failed replay
- **WHEN** replay targets stale bundle bytes and has a nonzero return code
- **THEN** both stale-target and failed-run facts are returned

#### Scenario: Ambiguous attachment with context
- **WHEN** a surface has competing declaration candidates and related DAG context
- **THEN** attachment is ambiguous while DAG evidence remains context-only

### Requirement: Negative evidence is open-world and non-promotional
The system SHALL include nonclaims explaining that observed absence is bounded by configured inputs and does not prove mathematical or Lean-level nonexistence.

#### Scenario: No configured replay provenance
- **WHEN** no replay artifact was configured for a surface
- **THEN** the result says replay was not observed and does not say replay failed

### Requirement: Coverage counts match query predicates
The system SHALL derive summary counts and returned rows from the same generation-scoped SQL predicates with deterministic caps and omissions.

#### Scenario: Truncated negative population
- **WHEN** unmatched surfaces exceed the result cap
- **THEN** returned count, total matched population, controlling cap, and truncation state are mutually consistent
