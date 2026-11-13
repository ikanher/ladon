# Source-only interpretation

Source: `../lean/matrix-factorization/latex/natural-language/poisson_fixed_participation_finite_bracket_proof.tex`, SHA-256 `7c82e6719baf1857b6e71691b8257292c42c20b914f5d3f70fe9fc49412a364b`, tracked and unchanged in the sibling checkout at selection. The present root auditor had read the abstract and setup before selecting this passage; no formal theorem, prior audit, or reference answer for this passage was inspected before this file was written. This is an exposed source audit, not a blinded discovery experiment.

Selected claim: the **Certified calibration interval** corollary (source lines 474–539), using the preceding finite-threshold bracket (lines 224–252) and product-law setup (lines 135–173).

The objects are two independent `T`-fold product laws: `Q_σ = N(0,σ²)^⊗T` and `P_σ = ((1-q)N(0,σ²)+qN(Δ,σ²))^⊗T`, with integer `T ≥ 0`, `0 ≤ q ≤ 1`, real `Δ`, real `ε ≥ 0`, and `0 ≤ δ ≤ 1`. The exact profile `Π_ε(σ)` is the maximum of both directed hockey-stick profiles and is defined even at `σ=0` using degenerate Gaussians. The feasible set is `S = {σ ≥ 0 : Π_ε(σ) ≤ δ}`; its infimum is taken after an upper certificate proves it nonempty.

For positive candidates `σ_L` and `σ_U`, a strict lower expression `δ < L_{σ_L}(ε,a_L)` and a non-strict upper expression `max(U_F, U_R)_{σ_U} ≤ δ` imply `σ_L ≤ inf S ≤ σ_U`. The thresholds may differ. A complete proof needs: (1) the lower expression really bounds the exact two-sided profile from below at `σ_L`; (2) the supplied upper expressions bound **both** directed profiles at `σ_U`; (3) the exact profile is nonincreasing as noise grows, including from zero; and (4) the infimum comparison uses the same feasible set and its nonemptiness, without assuming attainment. The informal monotonicity argument is adding common independent Gaussian noise of variance `σ₂²−σ₁²` to both product laws.

The formal counterpart's exact law, profile, zero-noise domain, monotonicity, certificate inequalities, and infimum target remain to be inspected. The source itself does not assert that the thresholds or bounds are optimal.
