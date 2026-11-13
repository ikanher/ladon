# Gaussian mechanism theorem: candidate positive-control review

## Decision

**Not yet eligible as a faithful positive control for source-to-owner evaluation.** The source theorem is a useful target, but the inspected Lean owners do not connect the arbitrary sensitivity-bounded statistic mechanism to the GDP profile. The source claim remains unresolved at that boundary. This is a mapping result, not a mathematical fault.

## Source claim

The frozen source is [GDP.tex](snapshot/paper/theory/mu-dp/fDP/GDP.tex), theorem `thm:g_mech`. It defines a statistic sensitivity over neighboring datasets, adds Gaussian noise with variance `sens(θ)^2/μ^2`, and claims the mechanism is `μ`-GDP. Its proof maps each neighboring output pair to equal-variance Gaussian laws with means `θ(S)` and `θ(S')`, identifies the pair's trade-off as `G_|θ(S)-θ(S')|/σ`, then uses the sensitivity bound and monotonicity in the GDP parameter to lower-bound it by `G_μ`.

## Inspected formal boundary

- [`GaussianDP.lean`](snapshot/Mf/DP/GaussianDP.lean) defines `GaussianDP μ`, its `gdpProfile`, and a trade-off/profile view. These are theorem-facing privacy abstractions; the inspected declarations do not take a statistic, neighboring relation, Gaussian output kernel, or sensitivity proof.
- [`GaussianApproxDP.lean`](snapshot/Mf/DP/GaussianApproxDP.lean) defines event-level `ApproxDP` for a mechanism and generic lemmas converting a privacy-loss-set integral bound into event-DP. This is not the source's GDP trade-off result.
- [`FiniteGaussianPrivacyBasis.lean`](snapshot/Mf/DP/FiniteGaussianPrivacyBasis.lean) includes a centered Gaussian event-`ApproxDP` transport theorem. It operates on a concrete pair of Gaussian measures and an already supplied event bound; it does not establish the source's arbitrary-statistic GDP theorem.
- A broader repository search found [`AdamFTRLGaussianBridge.lean`](../../../../../../lean/matrix-factorization/Mf/DP/AdamFTRLGaussianBridge.lean), which defines an explicit scalar Gaussian output measure and proves event-level `ApproxDP` from an update-sensitivity premise plus an assumed `gdpProfile ≤ δ`. This is a useful neighboring example of a law-level bridge, but it imports the profile bound as a premise and concludes approximate DP, not the source theorem's direct GDP trade-off. Its local literature anchors do not make it a formal counterpart of `thm:g_mech`.

The source-to-formal chain still needed is: define the neighboring Gaussian output laws from `θ` and the noise scale; prove their exact trade-off is the GDP curve with parameter `|θ(S)-θ(S')|/σ`; apply the sensitivity bound and monotonicity to obtain `G_μ`; package this uniformly over every neighboring dataset pair as the mechanism's GDP guarantee. The selected declarations do not close this chain. The Adam/FTRL bridge fills part of a related approximate-DP route but assumes the profile bound rather than deriving the exact GDP trade-off, so it does not qualify as the missing faithful control.

Snapshots and toolchain identity are recorded in [INPUTS.json](INPUTS.json). This was an informed root inspection; no independent review or Lean compilation was run for this candidate screen. The Adam/FTRL file was inspected in place but is outside the captured GDP source snapshot.

## Consequence for the next comparison

The Gaussian mechanism theorem cannot currently be used as the positive control for the hidden fixed-size subsampling map: both are missing a mechanism-to-privacy-object bridge in the inspected Lean surface. The fixed-size subsampling audit remains an unresolved support control. Before a paired source-to-owner exercise, select a claim whose Lean theorem actually binds the source mechanism/output law and privacy conclusion, or deliberately define a narrower control around an exact Gaussian-pair trade-off theorem if one exists and compile it. Do not score a profile definition or generic event-DP lemma as full support for `thm:g_mech`.
