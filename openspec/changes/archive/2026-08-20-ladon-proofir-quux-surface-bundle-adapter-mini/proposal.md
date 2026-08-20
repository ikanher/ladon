## Why

Quux's current ProofIR Lean surface extractor emits
`proof_ir_lean_surface_bundle`, while Ladon's bridge currently accepts only
`proofir_bridge_index`. Ladon needs a deterministic adapter for this compact
source-surface shape so Quux can supply useful evidence without exposing raw
ProofIR dialects to Ladon core.

## What Changes

- Add bridge input normalization for `proof_ir_lean_surface_bundle`.
- Convert bundle surfaces into compact bridge rows with declaration, source,
  authority, and replay-boundary metadata preserved where useful.
- Add frozen local fixtures based on representative Quux surface-bundle rows.
- Keep unsupported ProofIR artifact kinds rejected with explicit diagnostics.

## Capabilities

### New Capabilities

- `ladon-proofir-quux-surface-bundle-adapter`: Adapts compact Quux Lean surface
  bundles into Ladon's optional ProofIR bridge input contract.

### Modified Capabilities

None.

## Impact

- Affected code: `src/ladon/proofir_bridge.py`.
- Affected tests: ProofIR bridge fixture and normalization tests.
- Affected docs: ProofIR bridge input-boundary description.
