# Proposal

The Lean-backed smoke pass succeeded on several previously text-only roots and
the observed classifier noise has been calibrated. Expand the maintained root
matrix so these roots now exercise declaration-level analysis by default.

# Scope

- Convert these matrix entries from text-backed to Lean-backed:
  - `quux-bifr-rmse-problem`
  - `mf-gaussian-core`
  - `mf-bsr-factor-core`
  - `mf-optimization-ftrl`
- Preserve text-backed project/facade runs where declaration extraction is not
  the point.
- Rerun root-matrix regression after regeneration.

# Non-Goals

- No change to target repos.
- No conversion of every matrix entry to Lean-backed extraction.
- No new finding types.
