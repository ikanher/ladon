# Inventory v2: stable questions before r03 review

This exposed revision follows r02's already known sign finding. It is not a fresh first interpretation or blind discovery. Immutable source paths below are relative to ../pld-core-r01/inputs/. The 15-file input manifest is inherited unchanged. The original inventory is preserved; parent IDs retain their original meanings. Every listed original assertion remains visible, even when unresolved. Proposed verdicts are withheld from this inventory for the reviewer's first assessment.

Paper laws P,Q have densities pP,qQ and the source convention δ(P||Q)(ε)=sup_S[Q(S)−exp(ε)P(S)] (prelims.tex:13–16). Assertions range over real ε unless explicitly restricted. Probability normalization, extended-line endpoints and possible atoms are source context, not optional Lean assumptions.

| ID | Source file and span | Exact attributed question / context |
|---|---|---|
| P1 | PRV.tex:4–22, definition | Are the extended-real PRV pair definition, y(t)=exp(t)x(t), endpoint conventions and test-function version matched? Do not equate a real-measure structure with existence/uniqueness of these probability laws. |
| P2 | PRV.tex:27–39, thm:PRV_LLRV; appendix_PRV.tex:6–31 | Under P and Q respectively, does log(qQ/pP) produce X and Y representing δ(P||Q), with the source's singular/extended conventions? |
| P3.a | PRV.tex:43–49, eqn:delta_PRV_simple; appendix_PRV.tex:53–63 | Is δ(ε)=Pr(Y>ε)−exp(ε)Pr(X>ε)=E[(1−exp(ε−Y))_+] under the original laws? Preserve orientation and thresholds. |
| P3.b | Same theorem; appendix_PRV.tex:64–75 | Is the exponential-tail expression Pr(Y≥ε+Z) justified? Record Z's rate and independence needed for the stated smoothing identity. |
| P3.c | PRV.tex:50–54, eqn:PRV_from_delta; appendix_PRV.tex:73–81 | Does y(t)=δ″(t)−δ′(t) hold with classical derivatives/densities, and with what regularity? |
| P3.d | PRV.tex:53, eqn:PRV_from_delta | Does the printed x(t)=exp(t)(δ″(t)−δ′(t)) follow for the same pair? Keep any corrected expression as a separate claim. |
| P3.e | PRV.tex:57–59, remark | Does the stated reconstruction justify independence from the chosen representation and uniqueness, including endpoint masses? |
| P4 | PRV.tex:65–84, thm:composition_PRVs; prelims.tex:23–25 | Under independent sampling within each side, do the sums X1+X2,Y1+Y2 represent composed privacy curves? Match product laws and both loss orientations. |
| G1.a | centered-bridge-note.tex:26–72, Views A/B | For n≥1, σ>0, d∈R^n, ε∈R, is the event supremum the positive-part integral and attained by the stated likelihood-ratio halfspace? |
| G1.b | Same note:74–125, View C and “What must be matched exactly” | Is T=−〈d,y〉 Gaussian with means ∓r and variance σ²r, and does the threshold/CDF calculation give the printed profile for r>0, Δ=2√r? |
| G2.a | Same note:128–180, radial identity | Is the full event supremum equal to G(||d||²), with G(0)=(1−exp ε)_+? This retains the original inventory's radial question beyond the initial early passage. |
| G2.b | Same note:182–210, envelope/bridge seam | For Δ>0, is the radius-interval supremum H(Δ), and does this establish the stated equivalence? G(0) must be preserved; H was defined only for positive Δ. |
| S1 | Support only: FiniteGaussianPrivacy centered theorem, historical raw audit-check.log | Which restricted one-way event bound follows from the analytic condition for σ>0, ε≥0, Δ≥0, δ<1 and ||d||²≤(Δ/2)²? This adjacent support row cannot replace G1/G2. |

Completeness: split every displayed assertion in the three selected PLD theorem blocks and their uniqueness remark; retain the original Gaussian G1/G2 questions with corrected spans. General subsampling and mechanism examples in the appendix are excluded except the smooth Gaussian witness used to check P3.d. Later note sections (212 onward) are context, not separately audited theorems; the Δ=0 use of an only-positive-Δ H remains an unadjudicated boundary question. P1 existence and P3.e uniqueness need not be settled to close this bounded report, but must remain explicit unresolved rows.

Selection: P2 and P4 remain the intended characterization/composition obligations; P3.d is a consequential source-consistency check from r02. Original G1/G2 remain the control candidate; S1 is an explicitly narrower support result. No new production operation is selected.
