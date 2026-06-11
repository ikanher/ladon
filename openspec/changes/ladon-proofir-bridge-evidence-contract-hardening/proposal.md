## Why

External review approved the ProofIR/Quux normalization direction but found that
the review packet was source-incomplete and that several evidence-boundary edge
cases could weaken reviewer confidence. Ladon needs a hardening pass before this
bridge lane is treated as merge-ready evidence.

## What Changes

- Complete reviewer-facing quoted surface metadata by preserving `proofTrust`,
  `replayBoundary`, and extractor/source metadata in joined claim cards.
- Broaden stale-source diagnostics so hash drift is reported independently of
  the selected fallback join kind.
- Normalize snapshot anchor joins conservatively, including
  `source_line_anchor_decl`.
- Let bundle-level `source.sourcePath` and `source.contentHash` backfill surface
  rows when individual surfaces omit those fields.
- Harden malformed optional input handling and diagnostics for supported input
  kinds.
- Regenerate the pro review packet with changed transitive source dependencies,
  especially `src/ladon/atlas.py`.

## Capabilities

### New Capabilities

- `ladon-proofir-bridge-evidence-contract-hardening`: Tightens ProofIR bridge
  evidence preservation, stale-source diagnostics, malformed input handling, and
  review-packet completeness.

### Modified Capabilities

None.

## Impact

- Affected code: `src/ladon/proofir_input.py`, `src/ladon/proofir_bridge.py`,
  `src/ladon/atlas_workflow.py`.
- Affected tests: ProofIR bridge and atlas workflow regression tests.
- Affected packets: regenerated pro review bundle under `temp/`.
