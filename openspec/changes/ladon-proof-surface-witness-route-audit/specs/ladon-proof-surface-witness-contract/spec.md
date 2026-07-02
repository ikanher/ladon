## ADDED Requirements

### Requirement: Proof surface witness artifact
The system SHALL accept a compact proof-surface witness artifact containing
artifact kind/version, producer metadata, spec surfaces, proof endpoints,
no-drift gates, axiom audits, source pins, proof-hole policy metadata, and
nonclaims without requiring raw Lean verifier logs.

#### Scenario: Complete witness is supplied
- **WHEN** a supported proof-surface witness contains spec surfaces, proof endpoints, no-drift gates, axiom audits, source pins, proof-hole policy metadata, and nonclaims
- **THEN** normalization preserves those rows as quoted proof-surface route metadata

#### Scenario: Unsupported witness kind is supplied
- **WHEN** an input artifact has an unsupported kind, unsupported version, or malformed top-level shape
- **THEN** Ladon emits an optional-input diagnostic and does not fabricate proof-surface authority

### Requirement: Spec surface and proof endpoint roles
The system SHALL normalize declaration-level proof-surface roles without
hard-coding project names, including at least `lean_spec_stub`,
`lean_proof_endpoint`, and `lean_no_drift_gate`.

#### Scenario: Frozen spec stub role is supplied
- **WHEN** a witness row marks a declaration as `lean_spec_stub`
- **THEN** normalization preserves the declaration identity, source attachment metadata, role, and quoted proof-hole policy for downstream route audit

#### Scenario: Proof endpoint role is supplied
- **WHEN** a witness row marks a declaration as `lean_proof_endpoint`
- **THEN** normalization preserves the declaration identity, endpoint scope, source attachment metadata, and quoted proof authority metadata without promoting it to Ladon-owned proof truth

#### Scenario: Nonstandard module names are supplied
- **WHEN** a witness uses module names that do not contain conventional labels such as `Theorems`, `Solution`, or `Discharge`
- **THEN** normalization uses explicit witness roles rather than path-name heuristics to classify rows

### Requirement: No-drift gate metadata
The system SHALL normalize no-drift gate rows that connect a frozen spec surface
to a proof endpoint and quote the verifier context under which the gate was
observed.

#### Scenario: Identity gate links spec and endpoint
- **WHEN** a no-drift gate row names a spec declaration, a proof endpoint declaration, a gate declaration, a status, and verifier metadata
- **THEN** Ladon preserves the link as route-governance evidence and records the quoted status and verifier metadata

#### Scenario: Gate status is not clean
- **WHEN** a no-drift gate row has an unknown, failed, stale, or missing status
- **THEN** Ladon preserves the row and exposes the non-clean status for route diagnostics without treating the endpoint as clean

### Requirement: Source pin metadata
The system SHALL normalize source pins for witness rows, including source path,
source range when available, content hash, tool version, generated-at timestamp,
and pin status.

#### Scenario: Source hash pin matches a declaration
- **WHEN** a witness row has a content hash and declaration name that match Ladon declaration evidence
- **THEN** Ladon records high attachment confidence for that witness row

#### Scenario: Source pin is stale
- **WHEN** a witness row has a content hash that differs from the matched Ladon declaration evidence
- **THEN** Ladon records stale source attachment context and does not use the row as high-confidence proof-surface evidence

### Requirement: Axiom audit metadata
The system SHALL normalize axiom audit rows that quote the axiom footprint for a
proof endpoint or gate, including allowed axioms, suspicious axioms, unknown
axioms, audit command metadata, and audit status.

#### Scenario: Clean axiom audit is supplied
- **WHEN** an endpoint has an axiom audit row with status `clean` and no suspicious axioms
- **THEN** Ladon preserves the audit as quoted route metadata for downstream clean-endpoint classification

#### Scenario: Suspicious axiom appears
- **WHEN** an endpoint has an axiom audit row that includes suspicious or unknown axioms
- **THEN** Ladon preserves those axiom names and statuses for downstream diagnostics

### Requirement: Proof-hole quarantine metadata
The system SHALL normalize proof-hole policy metadata for spec stubs and other
declared quarantine surfaces, including allowed file scopes, marker counts, and
the rule that quarantined holes are not proof authority.

#### Scenario: Spec stubs contain allowed proof holes
- **WHEN** a witness marks proof holes as quarantined under a spec-stub role and source scope
- **THEN** Ladon records the quarantine metadata and does not treat the spec stub as a proof endpoint

#### Scenario: Proof holes escape quarantine
- **WHEN** a witness records proof holes outside an allowed quarantine scope or on a proof endpoint
- **THEN** Ladon preserves that violation for proof-surface route diagnostics

### Requirement: Witness nonclaims
The system SHALL preserve witness-level and endpoint-level nonclaims that state
what the witness does not prove or certify.

#### Scenario: Nonclaims are supplied
- **WHEN** a witness includes nonclaims about theorem truth, proof correctness, source attachment, mathematical scope, or verifier coverage
- **THEN** Ladon includes those nonclaims in proof-surface reviewer output
