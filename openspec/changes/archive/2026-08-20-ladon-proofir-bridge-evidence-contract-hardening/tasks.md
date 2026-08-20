## 1. Packet

- [x] 1.1 Validate `ladon-proofir-bridge-evidence-contract-hardening` with OpenSpec.

## 2. Implementation

- [x] 2.1 Preserve quoted ProofIR surface metadata in reviewer claims.
- [x] 2.2 Backfill bundle-level source metadata into missing surface fields.
- [x] 2.3 Broaden stale-source diagnostics across fallback join kinds.
- [x] 2.4 Treat `source_line_anchor_decl` snapshot joins as warning-oriented.
- [x] 2.5 Harden malformed input handling for non-dict payloads and diagnostics.

## 3. Review Packet

- [x] 3.1 Update run-state or packet wording so review-packet finalization is not contradictory.
- [x] 3.2 Regenerate pro review packet with `src/ladon/atlas.py` and transitive source dependencies included.

## 4. Verification

- [x] 4.1 Run targeted bridge and atlas workflow tests.
- [x] 4.2 Run `uv run pytest -q tests`.
- [x] 4.3 Run `uv run python scripts/python_quality.py --strict`.
