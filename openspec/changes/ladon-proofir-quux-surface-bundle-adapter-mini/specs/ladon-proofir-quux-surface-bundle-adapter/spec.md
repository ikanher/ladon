## ADDED Requirements

### Requirement: Accept Quux Lean surface bundles

The ProofIR bridge SHALL accept `proof_ir_lean_surface_bundle` payloads as
compact source-surface inputs and normalize them before declaration joining.

#### Scenario: Surface bundle joins by source hash

- **WHEN** a surface bundle row and a Ladon declaration row have the same
  declaration name, source path, and content hash
- **THEN** the bridge emits a high-confidence source-hash attachment join

### Requirement: Preserve quoted surface metadata

The adapter SHALL preserve claim id, declaration name, source path, source
range, content hash, authority, replay boundary, and proof-trust metadata when
those fields are present.

#### Scenario: Reviewer card quotes adapted claim status

- **WHEN** an adapted surface appears in a reviewer card
- **THEN** claim metadata is quoted from the input surface without being marked
  as established by Ladon

### Requirement: Unsupported ProofIR kinds are explicit

The bridge SHALL continue to reject unsupported artifact kinds with a diagnostic
instead of fabricating bridge surfaces.

#### Scenario: Unsupported artifact supplied

- **WHEN** a ProofIR input has an artifact kind outside the accepted compact
  contract
- **THEN** the bridge emits `proofir.malformed_bridge_index` and no joins
