## ADDED Requirements

### Requirement: Existing trust audit boundary
The system SHALL treat `proof_surface_witness` and claim-authority route audit
as the existing trust-audit mechanism and SHALL NOT define a competing proof
authority subsystem for proof-surface diagnostics.

#### Scenario: proof-surface witness route audit is available
- **WHEN** a claim route references proof-surface witness rows
- **THEN** Ladon routes the claim through the existing proof-surface diagnostics rather than a separate trust-audit implementation

### Requirement: Verifier handoff contract
The system SHALL define an optional handoff contract for project-local verifier
scripts that generate proof-surface witness rows from Lean checks such as build
status, source hashes, no-drift gates, and axiom-footprint commands.

#### Scenario: verifier output is supplied
- **WHEN** a project-local verifier emits a valid proof-surface witness with command, tool version, source hash, endpoint, gate, and axiom-audit metadata
- **THEN** Ladon consumes it as quoted route-governance evidence through the existing proof-surface witness normalization path

#### Scenario: verifier output is absent
- **WHEN** no verifier output is supplied
- **THEN** Ladon does not fabricate proof-surface authority and only reports missing evidence where a claim route explicitly requires that evidence

### Requirement: Axiom audit handoff metadata
The system SHALL preserve axiom-audit command, allowed/suspicious/unknown axiom
sets, status, source attachment, and replay-boundary metadata from verifier
handoff rows.

#### Scenario: suspicious axiom is quoted
- **WHEN** a verifier handoff row quotes a suspicious, unknown, or forbidden axiom
- **THEN** the existing proof-surface audit emits the suspicious-axiom diagnostic with the quoted command and axiom class

#### Scenario: clean axiom audit is quoted
- **WHEN** a verifier handoff row quotes a clean accepted axiom audit for an attached endpoint
- **THEN** Ladon can use that row to satisfy route-evidence completeness while stating that it does not validate theorem truth

### Requirement: Trust evidence completeness summary
The system SHALL expose a summary of proof-surface route-evidence completeness
for reviewer workflows without changing the existing diagnostic meanings.

#### Scenario: claim has incomplete proof-surface evidence
- **WHEN** a claim route requires proof-surface witness evidence but lacks a clean endpoint, no-drift gate, accepted axiom audit, or source attachment
- **THEN** Ladon includes a route-evidence completeness summary pointing to the existing proof-surface diagnostics
