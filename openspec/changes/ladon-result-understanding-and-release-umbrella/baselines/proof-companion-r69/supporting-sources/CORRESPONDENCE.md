# Fixed-epoch offset correspondence — proposed maintenance handoff

The proposed maintained declaration is
`Mf.DP.tendsto_poissonFixedEpochCalibratedStddev_offset` in
[Mf/DP/PoissonFixedEpochOffset.lean](../Mf/DP/PoissonFixedEpochOffset.lean).
The public large-batch facade imports it; the focused offset audit prints its
statement and transitive axioms. The mathematical maintainer has not yet adopted
this addition or taken responsibility for the proposed prose.

For fixed positive integer E, sensitivity Δ > 0, ε ≥ 0 and
0 < δ < 1 − exp(−E), along T = E + k for all natural k, the theorem proves
Δ/σ(E,T) − sqrt(2 log T) tends to Φ⁻¹(−log(1−δ)/E).
The capped rate min(1,E/T) equals E/T on this entire admissible tail.
Unfolding both calibration definitions and rewriting that exact rate identifies
the same calibrated standard deviation, with the same Δ, ε, δ and T.
Composition of the general schedule limit with k ↦ E+k supplies the limit.
No extra calibration-equality premise is introduced.

## Checking and acceptance boundary

The exact proposed source bytes passed the normal pinned Lake build of the offset
module, focused audit, public facade and public audit, followed by the complete
ordinary-tool recipe below. The fresh audit reports only `propext`,
`Classical.choice`, and `Quot.sound`. The [final compilation receipt](../latex/lean/poisson_fixed_epoch_offset_handoff_r64/compilation-final.json)
binds source bytes, commands and output. The normal build took 16.29 seconds and
reported 6.57 GiB maximum process RSS (not aggregate tree RSS).

Two earlier builds failed in the dependency while concurrent work was underway;
those receipts remain historical. After that work fixed the dependency, the normal
build and recipe passed. Human maintenance/editorial adoption remains pending.

## Document versions and scope

The original exposition is unchanged. The
[revised manuscript proposal](../latex/natural-language/poisson_fixed_epoch_large_batch_optimality_exposition_offset_proposal.tex)
changes only the offset proof paragraph. Its new document digest is bound by
[manifest-proposed.json](../latex/lean/poisson_fixed_epoch_offset_handoff_r64/manifest-proposed.json).
[assessment-offset-proposed.json](../latex/lean/poisson_fixed_epoch_offset_handoff_r64/assessment-offset-proposed.json)
is a new model-attributed reassessment of that paragraph, not human certification.
The [historical manifest](../latex/lean/poisson_fixed_epoch_offset_handoff_r64/manifest-historical.json)
and [r63 assessment companion](../latex/lean/poisson_fixed_epoch_offset_handoff_r64/assessments-historical-r63.json)
are retained unchanged. The old guide also remains historical. All retain their
original document identities; no old judgment has been resealed as current.
The generic `offset-limit` canonical target is unchanged. The adapter has ordinary
compilation evidence, not a newly captured canonical target.

Only offset correspondence is reassessed. Leading, variance, total-equivalence,
average-only coverage and whole-claim coverage are not promoted. This is neither
a finite-horizon inequality nor a uniform limit over changing E. Checking this
proposition does not certify the surrounding proof strategy or human understanding.

## Ordinary-tool recipe

Run from the matrix-factorization repository root, with its pinned toolchain:

```bash
lake build Mf.DP.PoissonFixedEpochOffset Mf.DP.PoissonFixedEpochOffsetAudit Mf.DP.PoissonFixedEpochLargeBatchOptimality Mf.DP.PoissonFixedEpochLargeBatchOptimalityAudit
lake env lean Mf/DP/PoissonFixedEpochOffset.lean
lake env lean Mf/DP/PoissonFixedEpochOffsetAudit.lean
```

Inspect the source, compare the printed statement with the manuscript component,
and compare the audit's transitive axioms with the permitted set above. If the
first command fails, resolve the dependency before claiming maintained acceptance;
do not silently substitute stored compilation for a fresh normal build.
The full example passed from the documented repository root. No private experiment
workspace, bespoke import path, search index or canonical registration is needed.

Ladon's existing `proof-search goal complete` is optional when a consumer needs
completion bound to a captured original goal. Use that operation's help and an
explicit pinned Lean/Lake pair; `proof-search complete` was an erroneous historical
pointer. Direct source and evidence reading is a supported route.

## Maintenance decision

The mathematical maintainer owns source placement, continued compilation, and
adoption of the prose. Review these exact proposed
bytes and accept or reject the handoff. Both original experimental proofs remain
immutable alternatives. No new interface or reader comparison follows from this
handoff; comparative Ladon benefit remains unestablished.
