## Why

Quux is actively evolving its ProofIR surface and bridge artifacts, while Ladon
currently accepts only one compact `proofir_bridge_index` shape. Ladon needs a
small roadmap for consuming the useful Quux evidence contracts without importing
raw ProofIR dialects or becoming an authority on theorem truth.

## What Changes

- Define the target compatibility lane for Quux-produced ProofIR surface
  artifacts:
  - first-class or adapter support for `proof_ir_lean_surface_bundle`
  - alias handling for `sourceHash` and `contentHash`
  - conservative handling of nested `sourceAnchor` rows
  - optional atlas import for already-rendered `ladon_proofir_bridge_snapshot`
- Split implementation into child packets so the bridge can improve without
  weakening Ladon's clean-core trust boundary.
- Require frozen Quux-derived fixtures for each supported input variant.
- Preserve the non-claim that source/hash/range joins establish attachment
  confidence only, not proof correctness or theorem validity.

## Capabilities

### New Capabilities

- `ladon-proofir-quux-input-normalization`: Governs how Ladon normalizes compact
  Quux ProofIR surface and bridge artifacts into review-routing evidence.

### Modified Capabilities

None.

## Impact

- Affected code: `src/ladon/proofir_bridge.py`, optional atlas bridge ingestion,
  CLI validation, and tests around ProofIR bridge fixtures.
- Affected artifacts: OpenSpec child packets, ProofIR bridge JSON fixtures, and
  bridge/atlas report examples.
- Affected workflow: Quux-generated ProofIR surfaces can be joined to Ladon
  declaration evidence through a normalized adapter contract instead of bespoke
  one-off packet scripts.
