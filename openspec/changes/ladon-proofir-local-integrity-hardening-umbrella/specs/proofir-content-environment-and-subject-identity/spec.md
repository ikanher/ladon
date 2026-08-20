## MODIFIED Requirements

### Requirement: Separate content and observation identities
The system SHALL distinguish raw file-digest identity, canonical content artifact identity, path/generation observation identity, environment identity, and executable identity using field-specific validated domains, and SHALL keep unchanged canonical content stable across database generations.

#### Scenario: Unchanged artifact in a new generation
- **WHEN** identical canonical artifact bytes are discovered under a new generation
- **THEN** the content artifact ID remains equal and the observation ID changes

#### Scenario: Raw file digest resembles a content ID
- **WHEN** a whole-file SHA-256 digest and a detached canonical artifact ID use the same textual digest spelling
- **THEN** typed APIs and validators retain their distinct domains and do not compare or substitute one as the other

### Requirement: Exact environment references
Semantic subject identity SHALL reference a content-addressed environment manifest containing prover/toolchain, dependency, compiled-module, option, trust, fingerprint-scheme, and selected-executable identities; authority-eligible live execution SHALL bind an explicit repository root and toolchain context consistent with that manifest.

#### Scenario: Toolchain changes
- **WHEN** a declaration name and display text are unchanged but its Lean toolchain identity changes
- **THEN** the environment reference and environment-scoped declaration identity differ

#### Scenario: Explicit executable conflicts with repository pin
- **WHEN** a requested absolute Lean or Lake executable is inconsistent with the selected repository's toolchain pin
- **THEN** the live operation fails before launching the checker and publishes no accepted semantic artifact

## ADDED Requirements

### Requirement: Explicit toolchain execution is fail-closed
An authority-eligible live Lean operation SHALL use resolved absolute executables, an explicit resolved repository working directory, verified toolchain-pin evidence, and a documented sanitized environment, and SHALL NOT silently fall back to ambient executable lookup.

#### Scenario: Ambient PATH shadows Lean
- **WHEN** an unrelated `lake` or `lean` is placed first on `PATH` while an explicit valid toolchain context is selected
- **THEN** the live operation invokes only the selected absolute executables and records their identities

#### Scenario: Convenience ambient selection
- **WHEN** a caller explicitly requests ambient tool discovery
- **THEN** the result labels the selection as ambient and does not assign the authority reserved for an explicitly selected pinned toolchain

