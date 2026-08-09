# proofir-attachment-and-link-observations Specification

## Purpose
TBD - created by archiving change proofir-attachment-and-link-observations. Update Purpose after archive.
## Requirements
### Requirement: One versioned attachment resolver
Bridge and SQLite ingestion SHALL use the same versioned resolver and candidate ordering.

#### Scenario: Bridge and database see the same inputs
- **WHEN** both surfaces receive identical declaration and source evidence
- **THEN** they emit the same candidates, selected attachment, method, and policy identity

### Requirement: Evidence-accurate attachment methods
Attachment method names SHALL correspond exactly to predicates proved by their evidence.

#### Scenario: Source hash matches but path differs
- **WHEN** source bytes match a declaration module but the supplied source path differs
- **THEN** the result does not claim an exact path/name/source-hash attachment

### Requirement: Retained candidates and decisions
Every attachment observation SHALL retain all bounded candidates, evidence, rejection reasons, freshness, resolver identity, and selection decision.

#### Scenario: Two exact-name declarations remain
- **WHEN** two candidates survive the strongest available evidence tier
- **THEN** the attachment is ambiguous and both candidates remain inspectable

### Requirement: Name-only is diagnostic
A name-only match SHALL be emitted as a diagnostic candidate and SHALL NOT become a selected attachment.

#### Scenario: Only basename agrees
- **WHEN** no environment, fingerprint, content, range, path, or module evidence agrees
- **THEN** the result reports a name-only diagnostic with no attachment

### Requirement: Attributable artifact links
Semantic artifact relationships SHALL be expressed inside canonical artifacts or as independently attributable link observations over content IDs.

#### Scenario: Manifest declares a relationship
- **WHEN** repository configuration connects two paths without artifact-owned content IDs
- **THEN** the relationship is labeled a manifest assertion and not canonical semantic linkage

### Requirement: No Quux dependency
Production attachment/link code and portable tests SHALL NOT import, execute, or require the Quux research repository.

#### Scenario: Quux is absent
- **WHEN** the portable attachment suite runs without a Quux checkout
- **THEN** every resolver and link-observation test passes
