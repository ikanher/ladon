# First interpretation of `thm:pair`

Written before reading the certificate, its guide, or the correspondence audit. Source read: `.codex/state/r04-reader/current-mf-source.tex`, lines 27–146.

## Objects

The note fixes a finite public record universe and record gradients `g_r : R^p → R^p`, each globally Lipschitz and bounded in norm by one. Datasets are subsets with add/remove adjacency. A public integer `N` is fixed independently of the private input. Utility is evaluated on a reference dataset of size `N`, with `∇f = N^{-1} Σ_{r=1}^N g_r`, bounded by one and `L`-Lipschitz. The initial position and algorithm parameters are public (lines 50–58).

Each age samples recordwise independent Bernoulli masks and an independent standard Gaussian vector. The release is the masked sum divided by fixed `B=qN`, plus `σ Z/B`; Adam updates first and second moments, applies finite age-dependent bias corrections, and updates position using coordinatewise root and division and an outside-root stabilizer (lines 60–80). The two runs are source `s` with `kn` updates, sampling rate `q`, normalizer `qN`, step `√h`, stabilizer `e₀/√h`, and exponential betas `exp(-λ_r h)`; target `t` with `n` updates, rate `kq`, normalizer `kqN`, step `√(kh)`, stabilizer `e₀/√(kh)`, and linearly transformed betas `1-k(1-exp(-λ_r h))`. Here `h=H/(kn)` (lines 90–105).

Each run uses the public calibration `a_priv=ceil(2 log(1/δ)/ε)+1` and `σ_i²=2T_i a_priv q_i²/ε`; the theorem asserts separate privacy for each run (lines 107–112, 135–137). Risk is the average over the original update ages `j=0,...,T-1` of `E ||∇f(x_j)||²`, equivalently an independent uniform original output age (lines 82–88).

## Assumptions and conclusion as stated

Parameters satisfy `H,e₀,λ₁,λ₂>0`, `λ₂<2λ₁`, integers `k,n≥1`, `0<q≤1/k`, `0<ε≤1`, `0<δ<1`, and the displayed mesh guards (lines 90–92, 107–110, 127–134): `h≤bar h≤1/(2k max λ_i)` and `h≤min{(2λ₁-λ₂)/(2(k+1)λ₁²), 4Hq²/[ε(a_priv-1)]}`. The stated bound is

`|R_t-R_s| ≤ 2L A_mem √(h/k) + E(h;1/q,L,2L) + E(kh;1/(kq),L,2L)`

with constants defined in lines 113–125 and the explicit `E` defined later in the note. It also claims the right side is `O(√h(1+log(1/h)))` as `n→∞` for the listed fixed parameters and gradient bounds (lines 138–145). This is closeness of expected risks, not their order or an optimizer (lines 152–155).

## Initial uncertainty / likely scope boundary

The theorem combines a two-run comparison, finite bias corrections and original-age averaging, separately calibrated privacy, a Poisson-sampling specialization of a one-run initialized coupling, and a linear-to-exponential memory transfer. From the theorem text alone I cannot tell whether a retained native DP-Adam certificate formalizes this exact paired statement, only a component (likely the single-run coupling), or a related mechanism with different normalization/privacy/output semantics. Need inspect the declared correspondence audit and the checked certificate before deciding reuse. This is a reading of the note's claim, not validation of its truth.
