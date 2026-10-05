# Companion-local supporting sources

These are unchanged copies from the historical r09 source archive. They support
offline reading, not a fresh check or a self-contained build. The current companion
and paragraph are reviewed editorial proposals; manuscript adoption is pending.

The primary artifact is [the revised companion](COMPANION.md).
Its original support note identifies workspace paths; use these copies offline:

- [Existing exposition](supporting-sources/tex/poisson_fixed_epoch_large_batch_optimality_exposition.tex):
  canonical experiment/calibrations; `thm:smallbatch`; `prop:average-uniform-bound`;
  fixed-participation calibration appendix and bibliography.
- [Proposed manuscript version](supporting-sources/tex/poisson_fixed_epoch_large_batch_optimality_exposition_offset_proposal.tex):
  historical r64 offset-paragraph proposal, not adoption of the new clarification.
- [Offset adapter](supporting-sources/Mf/DP/PoissonFixedEpochOffset.lean) and
  [general calibrated limit](supporting-sources/Mf/DP/FixedParticipationGaussianCalibrationAsymptotics.lean).
- [Rate/schedule](supporting-sources/Mf/DP/FixedParticipationRate.lean) and
  [fixed-epoch quantities](supporting-sources/Mf/DP/PoissonFixedEpochVariance.lean).
- [Historical compilation](supporting-sources/historical-support/compilation-final.json) and
  [historical proposed assessment](supporting-sources/historical-support/assessment-offset-proposed.json),
  with [its manifest](supporting-sources/historical-support/manifest-proposed.json).
- [Correspondence note](supporting-sources/CORRESPONDENCE.md) retains original project-relative
  paths. It concerns proposed historical adoption, not this companion's review.

Pinned metadata is in supporting-sources/build. The full imports and compiled dependencies are
omitted, so this is not a self-contained Lake project. Matching adapter bytes with
its receipt is not a fresh compiler check. The companion introduces no new
formal binding or assessment; the new variance explanation is conventional prose.
