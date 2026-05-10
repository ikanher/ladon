# Design

## Planned Runs

1. Project-level architecture run:

   ```bash
   bin/ladon --repo-root /home/codex/projects/lean/matrix-factorization \
     --root Mf --skip-build
   ```

2. BIFR owner declaration run:

   ```bash
   bin/ladon --repo-root /home/codex/projects/lean/matrix-factorization \
     --root Mf/DP/BIFRPackedProfileFiniteSumBounds.lean \
     --extraction-backend lean --lean-extraction-scope root
   ```

3. BIFR owner plus packet-evidence run:

   ```bash
   bin/ladon --repo-root /home/codex/projects/lean/matrix-factorization \
     --root Mf/DP/BIFRPackedProfileFiniteSumBounds.lean --skip-build \
     --packet-dir /home/codex/projects/lean/matrix-factorization/temp/bifr-p-dependence-theory-review-data-r37
   ```

## Pre-Registered Predictions

### Project-Level Matrix-Factorization

- The module graph should be acyclic.
- Module count should be approximately `529`, with most modules under `Mf/DP`.
- `Mf.lean` is intentionally narrow, so a project-level root may not behave as
  a whole-tree umbrella.
- Top fan-in should include `Mf.DP.Sensitivity`,
  `Mf.DP.PLDRandomAllocation`, `Mf.DP.ParticipationSetGaussianCore`, and
  `Mf.DP.GaussianDP`.
- Top fan-out should include `Mf.NTK`, `Mf.DP.BNB`, and selected DP bridge or
  BIFR owner surfaces.

### BIFR Packed-Profile Owner

- Direct import closure should be broad because
  `Mf.DP.BIFRPackedProfileFiniteSumBounds` imports
  `Mf.DP.BIFRProductObjectiveHalfSliceLowerWitness`.
- A root-import-closure hotspot and composite import-pressure finding should
  appear.
- Declaration-family hotspots should include suffixes like
  `ge_one_add_firstLag`, `nonneg`, `last`, `rev`, or `eq_forward`.
- Proof-family similarity candidates should appear for packed-profile sibling
  theorem families.
- Declaration fan-in should identify packed-profile index/term/sum helpers as
  shared proof kernels.

### Packet Evidence

- The r37 review-data packet should be detected as present.
- It is expected to be partial rather than complete because the packet is not a
  self-contained witness/checker bundle.
- It should still show owner-reference and tests/metadata style evidence.

## Falsification Conditions

- No BIFR proof-family candidates appear in the owner Lean-backed run.
- No direct import closure hotspot appears for the packed-profile owner.
- `Mf.DP.Sensitivity` is not near the top module fan-in surface.
- Packet evidence marks r37 complete despite missing witness/checker classes.
