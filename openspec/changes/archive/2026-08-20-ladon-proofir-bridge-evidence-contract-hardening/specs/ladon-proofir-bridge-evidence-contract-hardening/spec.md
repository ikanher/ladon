## ADDED Requirements

### Requirement: Reviewer claims preserve quoted surface metadata

The ProofIR bridge SHALL preserve available `proofTrust`, `replayBoundary`,
extractor guarantee, and source metadata in joined reviewer claim rows as quoted
metadata, not as Ladon proof evidence.

#### Scenario: Surface bundle claim is rendered

- **WHEN** an adapted surface bundle row joins to a Ladon declaration
- **THEN** the reviewer claim includes quoted proof-trust and replay-boundary
  metadata and does not mark the claim as established by Ladon

### Requirement: Stale-source drift is independent of fallback join kind

The ProofIR bridge SHALL emit stale-source diagnostics whenever a joined
surface and declaration have comparable declaration/source-path identity and
different source hashes.

#### Scenario: Stale hash falls back to source anchor

- **WHEN** a surface with a stale source hash joins by source-line anchor
- **THEN** the bridge emits `proofir.packet_stale_source`

#### Scenario: Stale hash falls back to module declaration

- **WHEN** a surface with a stale source hash joins by exact module/declaration
- **THEN** the bridge emits `proofir.packet_stale_source`

### Requirement: Bundle source defaults backfill missing surface fields

The surface-bundle adapter SHALL copy top-level `source.sourcePath` and
`source.contentHash` into surface rows only when those fields are absent from
the individual surface.

#### Scenario: Surface omits source fields

- **WHEN** a bundle surface omits source path and content hash but the bundle
  top-level source object contains them
- **THEN** the normalized surface can still join by source hash

### Requirement: Snapshot anchor joins remain warning-oriented

Atlas workflow SHALL keep name-only and source-anchor snapshot joins
warning-oriented, including `source_line_anchor_decl` and
`root_module_source_anchor`.

#### Scenario: Snapshot has source line anchor join

- **WHEN** a bridge snapshot join has `matchKind` equal to
  `source_line_anchor_decl`
- **THEN** atlas workflow reports low confidence and `warningOnly` true

### Requirement: Malformed optional ProofIR input is defensive

The bridge SHALL return a malformed optional-input report for unsupported or
non-object ProofIR payloads rather than raising an exception.

#### Scenario: Non-object ProofIR payload supplied

- **WHEN** a caller supplies a JSON list, string, number, or boolean as the
  optional ProofIR input
- **THEN** the bridge emits `proofir.malformed_bridge_index` and no joins

### Requirement: Review packets include transitive source dependencies

ProofIR bridge review packets SHALL include source dependencies required by the
included tests and workflow code.

#### Scenario: Atlas workflow tests are included

- **WHEN** a review packet includes `tests/test_atlas_workflow.py` and
  `src/ladon/atlas_workflow.py`
- **THEN** the packet also includes `src/ladon/atlas.py`
