## ADDED Requirements

### Requirement: Declaration surface comparison
The system SHALL compare before and after declaration surfaces and classify
declaration-level changes.

#### Scenario: Declaration is added or removed
- **WHEN** a declaration appears only in the after surface or only in the before surface
- **THEN** the changelog classifies it as added or removed and records declaration name, module, kind, source path, and available source evidence

#### Scenario: Declaration is renamed with stable surface
- **WHEN** a declaration name changes but module, kind, source range or hash evidence, and normalized theorem surface indicate the same declaration surface
- **THEN** the changelog classifies the row as a rename candidate and marks the confidence level used for the match

### Requirement: Theorem surface semantic classes
The system SHALL classify theorem-surface changes into bounded review classes
when sufficient before and after evidence is available.

#### Scenario: Proof changes but theorem type is stable
- **WHEN** theorem type evidence is unchanged but proof/source body evidence changes
- **THEN** the changelog classifies the change as proof-only or body-only and does not imply theorem truth was revalidated

#### Scenario: New assumption is added
- **WHEN** the after theorem surface contains an additional precondition compared with the before surface
- **THEN** the changelog classifies the change as added assumption and reports that prior unconditional claims may no longer be licensed by the theorem surface

#### Scenario: Conclusion appears weaker or stronger
- **WHEN** the conclusion comparison detects a possible weakening or strengthening
- **THEN** the changelog emits the class with heuristic confidence unless an elaborated backend supplies stronger theorem-type evidence

### Requirement: Source evidence on semantic changes
The system SHALL preserve source path, range, content hash, extraction backend,
extractor version, name-resolution method, and confidence where available on
semantic changelog rows.

#### Scenario: Source hash is available
- **WHEN** before and after declaration rows include content hashes
- **THEN** the changelog includes those hashes and uses them only as source attachment evidence

#### Scenario: Source evidence is missing
- **WHEN** a semantic row lacks source range or content hash evidence
- **THEN** the changelog still emits the row with reduced confidence and a diagnostic explaining the missing evidence

### Requirement: Nonclaim preservation
The system SHALL distinguish semantic theorem-surface changes from proof-truth
or proof-correctness claims.

#### Scenario: Theorem surface changes
- **WHEN** a theorem type, assumption, or conclusion changes
- **THEN** the changelog states only that the observed surface changed and does not claim either version is true

#### Scenario: External claim evidence is attached
- **WHEN** a changelog row includes ProofIR or Quux evidence
- **THEN** the row keeps that evidence in an external/quoted namespace and does not promote it to Ladon-validated proof authority
