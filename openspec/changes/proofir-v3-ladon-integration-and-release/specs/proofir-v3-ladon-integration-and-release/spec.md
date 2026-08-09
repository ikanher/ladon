## ADDED Requirements

### Requirement: Caller-neutral v3 CLI integration
Humans, scripts, editors, and models SHALL use the same ordinary Ladon CLI to query v3 evidence.

#### Scenario: Theorem dossier
- **WHEN** a caller requests a theorem dossier
- **THEN** the result separately reports claims, observations, derivations, attachments, coverage, navigation, and limitations

### Requirement: Explicit clean break
Legacy ProofIR artifacts SHALL be rejected before semantic projection and SHALL require regeneration as native-v3 artifacts.

#### Scenario: Legacy artifact is present
- **WHEN** indexing discovers a former ProofIR bridge, surface, replay, DAG, witness, or compatibility artifact
- **THEN** the result reports an attributable unsupported-legacy diagnostic and no dossier or database row derives from that payload

### Requirement: Explicit Lean execution
Lexical and stored-v3 queries SHALL NOT invoke Lean; checker refresh SHALL remain explicit, supervised, bounded, and represented as check-run observations.

#### Scenario: Warm stored query
- **WHEN** a stored theorem dossier or derivation slice is requested
- **THEN** no Lean process starts and freshness/coverage remain explicit

### Requirement: Operational contracts
Changed commands SHALL provide versioned schemas, stable exits, JSON stdout isolation, progress on stderr, caps, timeouts, atomic output, native-schema metadata, and exactly one terminal result.

#### Scenario: Checker timeout
- **WHEN** an explicit Lean check exceeds its timeout
- **THEN** the terminal observation reports timeout without publishing accepted evidence

### Requirement: Portable and external calibration
Release SHALL pass portable fixtures and installed-wheel gates before read-only calibration on Matrix-Factorization. Quux SHALL NOT be inspected, executed, imported, or used for calibration.

#### Scenario: Quux separation
- **WHEN** release and dependency gates run
- **THEN** they use Ladon-owned fixtures, never access Quux, and prove no runtime, build, package, test, or calibration dependency exists

### Requirement: Complete legacy removal
The release SHALL contain no converter command/module, direct legacy ingestion, legacy adapter projection, legacy fixture dependency, or legacy SQLite schema.

#### Scenario: Legacy route remains
- **WHEN** a source, installed CLI, test, schema, or database inspection finds a legacy ProofIR route
- **THEN** the release gate fails until that route is removed or rewritten against native v3
