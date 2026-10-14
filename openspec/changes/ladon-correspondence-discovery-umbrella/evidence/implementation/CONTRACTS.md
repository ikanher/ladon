# Exact local contracts and consumer questions

These findings are **answer-informed, model-authored source comparisons**. They reproduce known discrepancies; they are not fresh detection successes. Frozen primary passages and formal owner files are listed in source-inventory.json. No manuscript revision is adopted here.

## Inverse estimate

Original assertion: Lemma 8.6, equation (8.19), pages 95–96, for smooth zero-Haar-mean F on the two-dimensional torus and every integer m ≥ 0:

\[
\|N^{-1}F\|_{C_y^m}\le C_m\|F\|_{C_y^{m+4}}.
\]

Here the direction in N is fixed. Other parameters are held fixed; only the y variables are differentiated. The constant may depend on m and the fixed direction, but not on F. The maximum norm includes all torus derivatives through the stated order. The zero-mean condition selects the inverse solution; it is distinct from the quantitative derivative hypothesis.

The closest cited formal theorem is `NavierStokes.SmoothFamilyTorusInverse.norm_derivativeWord_inverse_le`, at line 1059. Its derivative word has length m. Its premises bound the source and its two pure coordinate derivatives of order **m+5** by the same C, at fixed parameter p. Its conclusion bounds the selected order-m output derivative by `mixedLossConstant m * C`. To produce a C^m norm comparison one takes a finite maximum over words/orders; the cited declaration is not itself that supremum theorem. `inverse_finiteJets`, line 865, independently requests `JetBound f S (n+5) C` with its constant chosen before f, S and C.

The formal proof applies `SmoothFourierData.coefficient_seminorm_bound` with p=m+1. That producer asks for p+4 derivatives and sums lattice weights of power −4. The prose uses the small-divisor loss of one power and sums power −3 using m+4 source derivatives. This is a concrete proof-route and guarantee difference.

**Finding:** the cited formal result does not directly establish the stated four-loss quantitative guarantee. Smoothness cannot supply a uniform higher-derivative norm bound in terms of a lower norm. We have neither refuted the prose bound nor proved that no other formal result establishes it.

**Consumer:** the physical updates in (8.20) and their class bounds in (8.21) use a finite derivative loss at every fixed output order. Because those classes control all fixed derivative orders, a five-loss theorem can plausibly support that class-level conclusion; this does not establish the exact four-loss estimate. The excerpt explicitly repeats “four additional derivatives” in its scaling argument. Keep the exact-estimate issue separate from the downstream class claim.

**Original missing obligation:** derive the m+4 estimate with constants independent of F, or supply an independently justified uniform bridge to the existing formal bound. A proposed five-loss revision changes the stated guarantee and would need its own reassessment. It is not completion of this obligation.

## Pressure flux

Original assertion: equation (10.19), pages 122–123, in the proof of Lemma 10.5. Set w=v−u, χ_R=φ_R^8, A_R=(∫χ_R|∇w|²)^(1/2), and B_R=||φ_R^4 w||_6. The prose claims, for almost every t and R≥1,

\[
\left|\int \pi w\cdot\nabla\chi_R\right|
\le C_T\left[R^{-1}(B_R+1)B_R^{1/2}+R^{-7/4}B_R^{3/4}\right].
\]

The constant may depend on T and the stipulated field bounds, but not R. The formal theorem `NavierStokesR3.PressureFlux.exists_uniform_actual_pressure_flux_bound`, line 576, chooses a single nonnegative CP before R and t and concludes

\[
\left|\int \pi w\cdot\nabla\chi_R\right|
\le CP\left[(B_R^{1/2}+1)(A_R/R+R^{-2})+R^{-7/4}B_R^{3/4}\right]
\]

for every t in the open time interval. Its premises include pressure-recovery hypotheses and uniform L2 difference, L3 reference-field, and L1 tensor-difference bounds. The sign conventions for both differences are reversed relative to the prose; the two sign changes cancel in the product. The definitions and weighting must be inspected, not matched by variable names alone.

The prose bounds the φ_R^4-weighted pressure using L^(3/2) Riesz boundedness, then pairs against a φ_R^3-weighted velocity. The formal `riesz_rTest_bound`, line 289, uses `RieszTestOperators.lpNorm_six_rieszTest_le`, line 223: L2 Riesz control followed by Sobolev bounds, with a derivative of the cutoff test. The derivative produces A_R/R+R^−2. Its tensor weighting is φ_R^2 and its test weighting is φ_R^5. This is a substantively different valid supporting route, not merely a changed display constant.

**Finding:** the exact intermediate bound and its argument differ. Equation (10.17), B_R≤C(A_R+R^−1||w||_2), supplies an upper bound for B_R using A_R. It does not bound A_R above using B_R and cannot eliminate A_R from the formal upper bound. No stronger converse is supplied in this comparison. The difference between almost-every-time and every-time also remains part of the contract; it does not repair the right-hand-side mismatch.

**Consumer:** the paper combines (10.17) and (10.19) with the energy identity, absorbs powers below two, then applies Gronwall. The formal consumer `R3/WholeSpaceUniqueness.lean` explicitly obtains the A_R-dependent pressure bound from this theorem. The formal proof can reach uniqueness through that bound while not following the paper's exact intermediate estimate. Final uniqueness must not be invoked to retrospectively clear its original stepping stone.

**Original missing obligation:** independently derive the paper's B_R-only estimate under its stated context. A replacement uniqueness argument using the formal estimate is a separate argument revision. Neither differing bounds nor an unsuccessful Lean application proves the informal estimate false.

## Review boundary

The inventory in COVERAGE.md retains the surrounding unexamined claims. Exact declaration lookup is lexical navigation only; live checks are captured separately. For both findings the correspondence interpretation is attributed to the assistant. Artifact validation, source identity and axiom policy cannot establish that interpretation.
