## ADDED Requirements

### Requirement: Compact route authority fields
The bridge input contract SHALL accept compact claim route fields for authority
auditing without requiring raw ProofIR dialect parsing.

#### Scenario: Claim row contains route metadata
- **WHEN** a supported `proofir_bridge_index` claim row contains `claimedAuthority`, `endpointScope`, `primaryTheoremSurfaces`, `supportingTheoremSurfaces`, `backgroundTheoremSurfaces`, `requiredEvidenceAuthorities`, `allowedExternalEvidence`, and `nonclaims`
- **THEN** Ladon normalization preserves those fields for route audit and reviewer-card output

#### Scenario: Unsupported raw ProofIR is supplied
- **WHEN** an unsupported raw ProofIR artifact kind is supplied
- **THEN** Ladon emits malformed optional-input diagnostics and does not fabricate route authority fields

### Requirement: Authority normalization
The bridge SHALL normalize authority fields to stable string lists or maps while
preserving unknown project-local labels.

#### Scenario: Authority is a string
- **WHEN** `claimedAuthority` or evidence authority is supplied as a string
- **THEN** normalization exposes it as a stable string value or one-item list according to the route schema

#### Scenario: Unknown authority is present
- **WHEN** a route row contains an unrecognized authority label
- **THEN** Ladon preserves the label and emits an unknown-authority diagnostic rather than treating it as Lean-closed

### Requirement: Required evidence authorities
The bridge SHALL preserve required evidence authorities by evidence name so the
route audit can compare premise authority against claimed status.

#### Scenario: Required scalar rows are imported
- **WHEN** `requiredEvidenceAuthorities` maps `scalarRows` to `imported_numeric`
- **THEN** reviewer output exposes `scalarRows` with authority `imported_numeric`

#### Scenario: Required Lean checker evidence is closed
- **WHEN** `requiredEvidenceAuthorities` maps `countMassEvidence` to `lean_checker`
- **THEN** reviewer output exposes the Lean checker authority without promoting it to theorem truth

### Requirement: Route metadata in bridge reports
Bridge reports SHALL carry route authority metadata in a quoted route-audit
section separate from source attachment joins.

#### Scenario: Claim has source attachment and route metadata
- **WHEN** a claim surface joins by source hash and also has route authority metadata
- **THEN** the bridge report keeps attachment confidence and route authority as separate fields

#### Scenario: Route metadata is used by atlas workflow
- **WHEN** an atlas workflow consumes a bridge report with route diagnostics
- **THEN** the workflow includes those diagnostics as review-routing evidence under a route or proofir namespace
