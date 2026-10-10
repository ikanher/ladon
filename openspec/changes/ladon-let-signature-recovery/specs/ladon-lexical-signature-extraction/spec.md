## Purpose

Provide bounded lexical declaration signatures that preserve supported statement expressions and expose extraction limits to search consumers.

## ADDED Requirements

### Requirement: Statement assignments are retained
Lexical extraction SHALL distinguish assignments within supported declaration types from the outer declaration body assignment. It SHALL retain consecutive and nested lets, binder defaults, and final conclusion text without including the proof body.

#### Scenario: Consecutive lets hide a query symbol
- **WHEN** a theorem contains consecutive lets and a queried symbol occurs only in the final conclusion
- **THEN** name search exposes that conclusion and type-text search finds the theorem

#### Scenario: Nested initializers and binder defaults
- **WHEN** a type includes a nested let initializer or a parameter default assignment
- **THEN** extraction retains the full supported signature and excludes proof-body-only tokens

### Requirement: Limits are explicit
Lexical extraction SHALL retain its byte ceiling and lexical authority. Unsupported or ambiguous signature boundaries SHALL produce visible incomplete or unavailable evidence rather than an apparently complete fragment.

#### Scenario: Byte ceiling
- **WHEN** a supported signature exceeds the configured lexical ceiling
- **THEN** its full byte count and truncation status remain accurate

#### Scenario: Unsupported syntax
- **WHEN** extraction cannot establish the supported signature boundary
- **THEN** a limitation is visible and no complete-looking signature is claimed

### Requirement: Extraction revisions refresh stored rows
Verified freshness SHALL account for extraction identity. Explicit update SHALL recover compatible recognized prior lexical extraction by re-extracting affected cached rows even without source edits, preserving retained evidence before replacement. Unknown extraction identities SHALL fail closed; no-op behavior SHALL remain byte stable for current inputs.

#### Scenario: Prior extractor without source edits
- **WHEN** a supported index was produced by the recognized previous extractor
- **THEN** it is not verified-fresh and explicit update refreshes its signatures, archives retained evidence, and publishes the new extraction identity without invoking Lean

#### Scenario: Unknown extractor
- **WHEN** an index reports an unrecognized extraction identity
- **THEN** update refuses rather than reusing its rows as current

### Requirement: Consumer guidance separates refresh operations
The consumer runbook SHALL distinguish changed-source lexical update, initial build and incompatible configuration/schema rebuild to a new path, and separate compiled-lineage acquisition.

#### Scenario: Ordinary source edits
- **WHEN** an author consults freshness guidance after editing Lean
- **THEN** the runbook directs status with changed modules and explicit update while keeping historical lineage distinct from new compiled evidence
