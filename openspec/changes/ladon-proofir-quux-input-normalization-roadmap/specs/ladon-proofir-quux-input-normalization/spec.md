## ADDED Requirements

### Requirement: Normalize compact Quux ProofIR surface inputs

Ladon SHALL define a normalized bridge-input contract for compact Quux ProofIR
surface artifacts and SHALL support `proof_ir_lean_surface_bundle` either
directly or through a deterministic adapter into the existing compact bridge
index shape.

#### Scenario: Surface bundle is supplied to the bridge

- **WHEN** a ProofIR input payload has `artifactKind` equal to
  `proof_ir_lean_surface_bundle` and surfaces with declaration name, source path,
  source range, content hash, authority, and replay-boundary metadata
- **THEN** Ladon can normalize those surfaces into bridge rows without requiring
  raw ProofIR dialect parsing or Lean replay

### Requirement: Preserve source-hash attachment confidence across field aliases

The bridge SHALL treat Quux `sourceHash` fields as aliases for `contentHash`
when evaluating declaration/source/hash attachment joins.

#### Scenario: Source hash alias matches declaration evidence

- **WHEN** a normalized ProofIR surface has `sourceHash` and a Ladon declaration
  row has the same declaration name, source path, and content hash
- **THEN** the bridge emits a source-hash attachment join with the same
  confidence and trust-boundary diagnostics as an equivalent `contentHash`
  surface

### Requirement: Source anchors are conservative evidence

The bridge SHALL preserve nested `sourceAnchor` evidence such as repository
path, packet path, start line, and line hash, but SHALL NOT promote a line anchor
to a full source-hash declaration join unless compatible declaration content
hash evidence is also present.

#### Scenario: Surface has line anchor but no content hash

- **WHEN** a ProofIR surface includes a nested `sourceAnchor` with path, start
  line, and line hash but no compatible declaration content hash
- **THEN** the bridge emits either a distinct source-anchor attachment join or a
  lower-confidence diagnostic, and does not emit `exact_source_hash_decl`

### Requirement: Unsupported ProofIR dialects remain out of core

Ladon SHALL reject or warn on unsupported raw ProofIR artifact kinds instead of
silently interpreting them as bridge inputs.

#### Scenario: Raw ProofIR dialect payload is supplied

- **WHEN** a payload has an unsupported ProofIR artifact kind outside the
  normalized bridge-input contract
- **THEN** Ladon reports that the input is unsupported and does not fabricate
  surfaces, claims, witnesses, or proof statuses

### Requirement: Bridge snapshots are optional atlas evidence

Atlas and reviewer workflows SHALL treat `ladon_proofir_bridge_snapshot`
summaries as optional already-rendered bridge evidence when supplied, and SHALL
keep compact surface inputs as the primary ProofIR bridge input contract.

#### Scenario: Bridge snapshot is supplied to atlas workflow

- **WHEN** an atlas workflow is given a `ladon_proofir_bridge_snapshot` with
  source Ladon report identity, joined surfaces, and bridge diagnostics
- **THEN** the workflow can summarize those joins and diagnostics as optional
  evidence without treating snapshot statuses as Ladon-validated proof truth

### Requirement: Quux fixtures are local and frozen

Ladon SHALL test Quux compatibility through small frozen fixture excerpts stored
inside the Ladon repository, not through live reads from `../quux`.

#### Scenario: Compatibility tests run in CI

- **WHEN** Ladon tests run without a sibling Quux checkout
- **THEN** the ProofIR input-normalization tests still cover the supported Quux
  artifact variants using local fixtures
