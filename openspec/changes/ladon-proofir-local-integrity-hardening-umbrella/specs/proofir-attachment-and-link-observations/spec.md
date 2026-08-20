## MODIFIED Requirements

### Requirement: Attributable artifact links
Semantic artifact relationships SHALL be expressed inside canonical artifacts or as independently attributable link observations over validated content artifact IDs. A link observation SHALL expose a discovered endpoint's raw bytes as `resolvedFileDigest` and SHALL expose `resolvedArtifactId` only when native artifact validation has established the detached canonical ID; diagnostics SHALL compare identities only within the same domain.

#### Scenario: Manifest declares a relationship
- **WHEN** repository configuration connects two paths without artifact-owned content IDs
- **THEN** the relationship is labeled a manifest assertion and not canonical semantic linkage

#### Scenario: Cataloged file is not a valid native artifact
- **WHEN** discovery computes a file digest but native ProofIR validation cannot establish an artifact ID
- **THEN** the endpoint contains `resolvedFileDigest`, has no `resolvedArtifactId`, and does not report artifact-ID drift

#### Scenario: Declared artifact ID disagrees with validated envelope
- **WHEN** a manifest endpoint declares an artifact ID different from the validated native artifact's detached ID
- **THEN** the observation reports artifact-ID drift without comparing the declaration to the whole-file digest

## ADDED Requirements

### Requirement: Incorrect link identity shape is rejected
The current link-observation policy SHALL reject the legacy shape in which a whole-file digest is supplied as `resolvedArtifactId`, and disposable projections SHALL be rebuilt rather than interpreting the old field heuristically.

#### Scenario: Legacy derived observation is loaded
- **WHEN** a derived link observation uses the superseded policy and provides no domain-accurate endpoint fields
- **THEN** validation rejects or regenerates it and never promotes the legacy value to a canonical artifact ID

