## ADDED Requirements

### Requirement: Ordinary CLI exposes all stored evidence projections
The system SHALL expose theorem dossier, artifact evidence, route/tree, and repository triage through caller-neutral `ladon proof-search evidence` subcommands.

#### Scenario: Installed help
- **WHEN** a user invokes installed help for each selector
- **THEN** exact arguments, bounds, format, output, freshness, and refresh behavior are documented without LLM-specific terminology

### Requirement: Text and JSON render the same result dictionaries
The system SHALL render section-aware compact text and canonical JSON from the same versioned result, including coverage, freshness, authority, diagnostics, omissions, truncation, and nonclaims.

#### Scenario: Theorem dossier parity
- **WHEN** the same dossier is rendered as text and JSON
- **THEN** every semantic section and negative-evidence state is represented in both formats

#### Scenario: Output-byte cap
- **WHEN** a result would exceed the configured output limit
- **THEN** the command emits a valid bounded result or fails before writing, never partial corrupt JSON

### Requirement: Warm evidence queries are read-only
The system SHALL open the project-local index read-only and SHALL never invoke Lean, Lake, replay commands, checkers, or generators implicitly.

#### Scenario: Stale index
- **WHEN** a warm evidence query detects stale or missing index state
- **THEN** it refuses or reports explicit stale coverage and directs the caller to the ordinary explicit build command

### Requirement: Portable integration fixtures cover the combined workflow
The system SHALL test build, status, dossier, artifact, forward/reverse routes, triage, text/JSON parity, and unchanged rebuild through installed entry points.

#### Scenario: Portable mixed-evidence repository
- **WHEN** the fixture contains exact, claim-only, ambiguous, stale, conditional, cyclic, and unsupported evidence
- **THEN** all commands return the preregistered authority-preserving predicates and the database remains valid

### Requirement: Real-repository calibration is fingerprinted and predicate-based
The system SHALL provide opt-in read-only Quux and Matrix-Factorization calibration that records repository/worktree/config/artifact/index identities, commands, timings, and semantic predicates.

#### Scenario: Quux CDC calibration
- **WHEN** calibration queries the CDC theorem and obligation routes
- **THEN** explicit surfaces/replays and authority transitions are reconstructed while nearby unattached context remains unattached

#### Scenario: Matrix-Factorization duplicate names
- **WHEN** calibration samples duplicate declaration names
- **THEN** source evidence is required for selection and timing alone cannot mark the calibration successful

### Requirement: Documentation and skill use verified installed commands
The system SHALL update repository documentation and the authoritative Ladon skill only after examples pass installed-wheel command checks.

#### Scenario: Checked examples
- **WHEN** documentation and skill command snippets are tested
- **THEN** they use the final ordinary CLI grammar and project-local database location
