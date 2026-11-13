# Finite Gaussian bracket: calibrated-noise consequence

## Result

The selected [source corollary](SOURCE.tex) says that a strict lower certificate at positive `σ_L` and a non-strict two-sided upper certificate at positive `σ_U` enclose the infimum of feasible noise standard deviations. **No fault was established in this bounded audit.** The [formal theorem](formal/Mf/DP/SampledGaussianFiniteBracketCalibration.lean), `sampledGaussian_calibration_interval_of_finiteBracketWithThresholds_certificates`, has the same three independently supplied thresholds, strict lower inequality, non-strict upper inequality, and interval conclusion. Its proof obtains feasible-set nonemptiness from the upper certificate and uses antitonicity of the exact two-sided profile for the lower endpoint; it does not assume the infimum is attained.

The source-only interpretation was frozen in [FIRST.md](FIRST.md) before inspecting the formal owner. [INPUTS.json](INPUTS.json) binds the tracked, unchanged source bytes at sibling commit `50810c9`; [FORMAL-INPUTS.json](FORMAL-INPUTS.json) binds twelve selected formal/metadata files. This is an informed root audit, not independent adjudication or a Ladon-versus-ordinary-Lean comparison.

## Obligation map

| Source obligation | Inspected formal evidence | Outcome |
| --- | --- | --- |
| Exact profile is the maximum of both directed hockey-stick profiles for the independent product laws. | `binaryAccountingProfile`, `sampledGaussianSourceProductLaw`, `sampledGaussianReferenceProductLaw`, and `sampledGaussianProductProfileStddev`. | Definitions align with the selected source objects: Bernoulli shift plus centered Gaussian in each coordinate, independent finite product, variance `σ²`, and both directions. |
| Maximum-coordinate witness `L(ε,a_L)` is a lower bound at `σ_L`. | `sparseGaussianProductMaximumEventForwardLowerBoundReal` and `sampledGaussianProductMaximumEventLowerBound_le_binaryProfile`. | The formula is `[(1-p_P)-e^ε(1-p_Q)]_+`; the formal theorem requires `σ_L>0` for standardized shift `Δ/σ_L`. |
| Forward and reverse formulas jointly upper-bound the exact profile at `σ_U`. | `sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBoundReal`, `sparseGaussianProductReverseBestUpperBound`, and `sampledGaussianProductBinaryProfile_le_finiteProfileUpperBoundWithThresholds`. | The retained first/second moments, residual cap, reverse dual/floor minimum, and maximum of two directions match the displayed source structure. Separate forward and reverse thresholds are supported. |
| More noise cannot increase the exact profile, including from `σ=0`. | `sampledGaussianProductProfileStddev_antitone` and `sampledGaussianProductProfile_variance_antitone`. | The proof maps both product laws through the same independent residual Gaussian vector. It accepts nonnegative `small ≤ large`; Mathlib's `gaussianReal_zero_var` identifies variance zero with a Dirac law. |
| A strict violation at `σ_L` and feasibility at `σ_U` bound the feasible-set infimum without attainment. | `sampledGaussian_candidate_infeasible_of_maximumEvent_certificate`, `sampledGaussian_feasibleSet_nonempty_of_upper_profile_certificate`, `le_sampledGaussianCalibratedStddev_of_not_feasible`, and the final interval theorem. | The upper certificate supplies nonemptiness. Upward closure rules out any feasible point below `σ_L`, and the infimum inequality follows in `NNReal`. |

The source uses nonnegative real standard deviations and the Lean API uses `NNReal`; this is the manual object map in this audit. The final Lean theorem does not require extra restrictions on `T`, `ε`, `δ`, or sensitivity beyond source assumptions; it only takes `q≤1` and positive candidate noise. The source's finite formulas apply at positive candidate noise, while the feasible-set profile itself includes zero. Neither the manuscript nor the inspected theorem claims optimal thresholds or that the endpoint is attained.

## Verification and boundary

- `lake env lean Mf/DP/SampledGaussianFiniteBracketCalibration.lean` exited 0 in the sibling's pinned Lake environment. Its stored `.olean` was newer than the selected source at inspection; this was a focused source check, not a complete dependency rebuild.
- [Check.lean](Check.lean) imported the owner and printed the exact final theorem, lower/upper bridges, monotonicity, and zero-variance lemma. Its [stdout](Check.stdout) reports only `propext`, `Classical.choice`, and `Quot.sound` for the final interval theorem, finite upper bridge, and monotonicity.
- Source and selected formal snapshots matched current sibling bytes when frozen. The retained [checksums](SHA256SUMS) identify the audit artifacts. The selected formal snapshot omits the full import closure.

This exercise verifies a meaningful real-source application under the original product-law assumptions. It does not test discovery of an unknown fault or show incremental benefit from Ladon's native interface. The next work should target a source-to-formal interpretation question that ordinary Lean proof checking leaves unresolved, with a concrete prediction of what Ladon adds; repeating another already matched corollary would have little value.
