## ADDED Requirements

### Requirement: Route audit model
The system SHALL normalize claim route rows containing claimed status, claimed
authority, endpoint scope, theorem surfaces, required evidence authorities,
allowed external evidence, and nonclaims without treating any row as theorem
truth.

#### Scenario: Complete route row is audited
- **WHEN** a claim route row includes `claimId`, `claimedStatus`, `claimedAuthority`, `endpointScope`, `primaryTheoremSurfaces`, `requiredEvidenceAuthorities`, `allowedExternalEvidence`, and `nonclaims`
- **THEN** the audit preserves those fields in reviewer output and marks them as route governance metadata

#### Scenario: Route metadata is absent
- **WHEN** a claim has quoted ProofIR status but no route authority metadata
- **THEN** the audit emits a missing-route-context diagnostic rather than inferring full closure

### Requirement: Closed claim with imported evidence diagnostic
The system SHALL emit `ladon.claim.closed_with_imported_evidence` when a claim
advertises closed or Lean-closed status while a required premise route uses
imported or external evidence authority not explicitly allowed by the claim.

#### Scenario: Lean-closed claim depends on imported interval evidence
- **WHEN** `claimedStatus` is `lean_closed` and `requiredEvidenceAuthorities` contains `imported_interval_certified`
- **THEN** the audit emits `ladon.claim.closed_with_imported_evidence` and reports the imported premise name and authority

#### Scenario: Conditional route is honestly labeled
- **WHEN** a claim status or authority records `conditional_external_evidence` and the imported evidence appears in `allowedExternalEvidence`
- **THEN** the audit does not emit `ladon.claim.closed_with_imported_evidence` for that imported evidence

### Requirement: Endpoint scope overclaim diagnostic
The system SHALL emit `ladon.claim.endpoint_scope_overclaim` when a claim
advertises a stronger configured endpoint scope than the observed primary theorem
route supports.

#### Scenario: Arbitrary-neighbor claim has sampled-null primary theorem
- **WHEN** a claim advertises `endpointScope` equal to `arbitrary_neighbor_event_dp` and the joined primary theorem surface records `sampled_null_event_dp`
- **THEN** the audit emits `ladon.claim.endpoint_scope_overclaim`

#### Scenario: Endpoint scope is consistent
- **WHEN** the claim endpoint scope and observed primary theorem route scope are equal
- **THEN** the audit records `scope_consistent` and does not emit an endpoint-scope overclaim diagnostic

### Requirement: Evidence authority mismatch diagnostic
The system SHALL emit `ladon.evidence.authority_mismatch` when artifact or claim
metadata advertises production or fully proved authority while route rows contain
diagnostic, smoke, unchecked, interval-certified, imported numeric, or external
certificate authorities that are not allowed for that claim.

#### Scenario: Production artifact contains smoke authority
- **WHEN** an artifact claims production or fully proved authority and a required evidence row has authority `smoke`
- **THEN** the audit emits `ladon.evidence.authority_mismatch` with the evidence row identity

#### Scenario: External authority is explicitly allowed
- **WHEN** a claim lists an external evidence row in `allowedExternalEvidence`
- **THEN** the audit preserves the external authority in the observed route and does not upgrade it to Lean-closed authority

### Requirement: Missing primary theorem surface diagnostic
The system SHALL emit `ladon.claim.missing_primary_theorem_surface` when a public
claim has no joined primary theorem surface or only helper/background theorem
surfaces.

#### Scenario: Public endpoint lacks primary theorem
- **WHEN** a claim declares a public endpoint but `primaryTheoremSurfaces` is empty
- **THEN** the audit emits `ladon.claim.missing_primary_theorem_surface`

#### Scenario: Primary theorem joins by source hash
- **WHEN** a primary theorem surface joins to a Ladon declaration by source hash and declaration name
- **THEN** the audit records the attachment confidence and does not emit the missing-primary theorem diagnostic

### Requirement: Route audit nonclaims
The system SHALL state that route audit diagnostics evaluate authority/evidence
alignment and SHALL NOT claim theorem falsehood, theorem truth, proof
correctness, or witness adequacy.

#### Scenario: Mismatch diagnostic is emitted
- **WHEN** any claim authority diagnostic is emitted
- **THEN** the diagnostic text states that Ladon found a claim/evidence route mismatch, not a proof invalidation
