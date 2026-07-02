## ADDED Requirements

### Requirement: Proof surface route join
The system SHALL join normalized proof-surface witness rows to claim routes and
Ladon declaration/source evidence while preserving source attachment confidence
separately from proof authority.

#### Scenario: Proof endpoint joins by source hash
- **WHEN** a claim route names a proof endpoint and the witness endpoint joins to a Ladon declaration by declaration name and content hash
- **THEN** the route audit records the endpoint with high attachment confidence and quoted proof-surface metadata

#### Scenario: Proof endpoint joins weakly
- **WHEN** a witness endpoint only joins by module/declaration name, basename, or source-line anchor
- **THEN** the route audit records the weak attachment and does not use it to clear high-confidence proof-surface requirements

### Requirement: Spec stub authority diagnostic
The system SHALL emit `ladon.proof_surface.spec_stub_used_as_authority` when a
public claim cites a frozen spec stub as proof authority or as its primary
proof-backed endpoint.

#### Scenario: Claim cites spec stub as endpoint
- **WHEN** a claim route lists a primary theorem surface whose witness role is `lean_spec_stub`
- **THEN** Ladon emits `ladon.proof_surface.spec_stub_used_as_authority` and reports the spec declaration and claim id

#### Scenario: Claim cites proof endpoint instead of spec stub
- **WHEN** a claim route lists a primary theorem surface whose witness role is `lean_proof_endpoint`
- **THEN** Ladon does not emit the spec-stub authority diagnostic for that surface

### Requirement: Missing no-drift gate diagnostic
The system SHALL emit `ladon.proof_surface.missing_no_drift_gate` when a claim
requires a spec-to-proof no-drift gate but no clean gate row links the relevant
spec surface and proof endpoint.

#### Scenario: Proof endpoint lacks required gate
- **WHEN** a claim route requires proof-surface drift protection and no clean no-drift gate links its spec surface to its proof endpoint
- **THEN** Ladon emits `ladon.proof_surface.missing_no_drift_gate`

#### Scenario: Clean gate links spec and endpoint
- **WHEN** a clean no-drift gate links the claim's spec surface and proof endpoint with acceptable source attachment
- **THEN** Ladon records the gate and does not emit the missing-gate diagnostic

### Requirement: Missing axiom audit diagnostic
The system SHALL emit `ladon.proof_surface.missing_axiom_audit` when a claim
requires an axiom footprint but no accepted axiom audit row exists for its proof
endpoint or required gate.

#### Scenario: Public endpoint has no axiom audit
- **WHEN** a public claim route requires axiom evidence and the joined proof endpoint has no axiom audit row
- **THEN** Ladon emits `ladon.proof_surface.missing_axiom_audit`

#### Scenario: Endpoint has clean axiom audit
- **WHEN** a proof endpoint has an accepted clean axiom audit row
- **THEN** Ladon records the audit and does not emit the missing-axiom-audit diagnostic for that endpoint

### Requirement: Suspicious axiom diagnostic
The system SHALL emit `ladon.proof_surface.suspicious_axiom` when an axiom audit
quotes suspicious, unknown, forbidden, or project-disallowed axioms.

#### Scenario: Suspicious axiom is quoted
- **WHEN** an axiom audit row includes a suspicious, unknown, or forbidden axiom
- **THEN** Ladon emits `ladon.proof_surface.suspicious_axiom` and reports the endpoint, axiom name, and quoted audit status

#### Scenario: Only allowed axioms are quoted
- **WHEN** an axiom audit row contains only project-allowed axioms and has clean status
- **THEN** Ladon does not emit a suspicious-axiom diagnostic for that endpoint

### Requirement: Clean endpoint classification
The system SHALL emit or expose `ladon.proof_surface.clean_endpoint` as a
reviewer-facing route classification when a proof endpoint has acceptable
attachment, required no-drift gates, required axiom audits, and no suspicious
proof-surface diagnostics.

#### Scenario: Endpoint route is complete
- **WHEN** a proof endpoint joins with acceptable source attachment and has all required clean gates and axiom audits
- **THEN** Ladon exposes `ladon.proof_surface.clean_endpoint` as quoted route-governance evidence

#### Scenario: Endpoint route has missing evidence
- **WHEN** a proof endpoint lacks required source attachment, gate evidence, or axiom audit evidence
- **THEN** Ladon does not classify the endpoint as clean

### Requirement: Frozen spec hub classification
The system SHALL emit or expose `ladon.proof_surface.frozen_spec_hub` for
modules or declarations that intentionally aggregate frozen spec stubs and are
not proof authority.

#### Scenario: Frozen spec hub imports many endpoints
- **WHEN** a module is identified by witness rows or role metadata as a frozen spec hub with spec stubs and allowed quarantined proof holes
- **THEN** Ladon classifies the module as `ladon.proof_surface.frozen_spec_hub` instead of reporting it only as generic proof-hole pressure

#### Scenario: Ordinary proof endpoint module has proof holes
- **WHEN** a module with proof endpoint roles contains unquarantined proof holes
- **THEN** Ladon does not classify it as a frozen spec hub and preserves the proof-hole route diagnostic context

### Requirement: Proof-surface trust boundary
The system SHALL state that proof-surface witness diagnostics evaluate route
evidence, source attachment, and quoted verifier metadata only, and SHALL NOT
claim theorem truth, proof correctness, witness adequacy, or mathematical scope.

#### Scenario: Proof-surface diagnostic is emitted
- **WHEN** any `ladon.proof_surface.*` diagnostic or classification appears in reviewer output
- **THEN** the output states that Ladon is auditing the evidence route and not validating theorem truth
