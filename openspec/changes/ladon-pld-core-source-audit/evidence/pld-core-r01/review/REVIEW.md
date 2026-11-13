# Independent source review (frozen inputs)

**Reviewer:** Codex independent reviewer  
**Basis:** `inputs/MANIFEST.json` and frozen copies under `inputs/paper` and `inputs/Mf` only. No findings/evidence documents or live sibling checkout were read. This is an exposed review; no fault was presumed.

## P2 — privacy-curve characterization

The paper statement is `PRVprivacycurve` (label `thm:PRV_privacycurve`) in frozen `paper/theory/numerical-composition/PRV.tex`. It asserts the hockey-stick/profile identity
`δ(ε) = Pr[Y>ε] − e^ε Pr[X>ε] = E_Y[(1−e^(ε−Y))_+] = Pr[Y≥ε+Z]`, with `Z` exponential, and conversely the densities `Y(t)=δ''(t)−δ'(t)` and `X(t)=e^t(δ''(t)−δ'(t))`. Appendix proof differentiates the tail-integral formula twice. As written, the converse is a density-level claim: it presupposes a twice differentiable curve and density/tail regularity sufficient for differentiation and the displayed integrals. The nearby definition explicitly discusses discrete and mixed PRVs, but this derivative formula does not cover those cases without additional measure/distributional formulation.

The frozen Lean owner files provide adjacent pieces, not a direct formalization of this theorem. `PrivacyLossCore.dp_event_bound_of_privacyLossSet`, `privacyLossSet_bound_of_dp_event_bound`, and `privacyLossSet_bound_iff_dp_event_bound` establish the measurable-event/hockey-stick positive-region characterization for measurable integrable densities on a shared base measure. `Profile/ConcretePLDPair.expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local` identifies a concrete log-loss pushforward profile with the source-space integral gap. `PLDCompositionApproxDP.concretePLDPair_sharedBaseProduct_eq_compFamily` and profile consumers transport/consume concrete PLD profiles under their stated shared-base product hypotheses. These are not the paper's general PRV converse, the exponential-tail identity, or `δ''−δ'` recovery theorem. No exact Lean theorem identifier/type for those general claims exists in the frozen owner files reviewed.

**Assessment:** formalization/scope gap, not an established mathematical fault. The paper's converse needs explicit smoothness and density assumptions to be a theorem in its stated form; the source itself says it assumes PDFs for ease of exposition while separately allowing discrete/mixed variables. That is an imprecision of scope, but this review does not establish that the intended continuous-density claim is false.

## P4 — Gaussian mechanism PRVs

The appendix proposition `Gaussian Mechanism` states that for `δ(N(μ,1)||N(0,1))`, `X=N(−μ²/2, μ²)` and `Y=N(μ²/2, μ²)`. Its proof computes `log(Q/P)=μ²/2−μt` under `t~Q`; the reverse variable under `P` is `−μ²/2−μZ`. These signs and means are consistent. The written statement should be understood with its degenerate case: at `μ=0`, both laws are the point mass at zero (the notation `N(0,0)`), not an ordinary positive-variance density.

The frozen Lean sources contain scalar analytic Gaussian endpoint definitions and event-bound formalization, rather than these PRV-law equalities. `GaussianPrivacyLoss.analyticGaussianExpr_eq_event_form` identifies the analytic expression with standard-normal CDF measures on `Iic` endpoints; `analyticGaussianExpr_eq_gaussianReal_event_form` / `_explicit` identify it with corresponding Gaussian event expressions. `FiniteGaussianPrivacy.gaussianPair_eventApproxDP_centered_of_analyticCondition_lt_one` has the exact centered implication: assumptions `0<σ`, `0≤ε`, `0≤Δ`, `sqDist d 0 ≤ (Δ/2)^2`, `analyticGaussianCondition Δ σ ε δ`, and `δ<1` imply for every measurable event `s`, `measure σ d s ≤ exp(ε) * measure σ (-d) s + ofReal δ`. The uncentered `gaussianPair_eventApproxDP_of_analyticCondition_lt_one` similarly assumes `sqDist μ μ'≤Δ²` and concludes the directed event inequality for `μ,μ'`. The argument reduces the nonzero-distance case through the explicit scalar endpoint/positive region and handles zero distance separately.

These types prove the event-level Gaussian control for finite isotropic Gaussian measures and are materially relevant to the centered bridge. They do not prove the exact PLD/PRV laws in P4, nor do they state equality of the supremum over events with the endpoint expression. The scalar premise is supplied externally as `analyticGaussianCondition`; `δ<1` is additionally needed by this theorem surface, and its epsilon premise is nonnegative. Thus they are a suitable formal control for the one-way “scalar endpoint implies all measurable events” bridge, but not a formal replacement for the paper's P4 PRV distribution claim.

## Open frontiers and audit scope

- General PRV definition and equivalence for arbitrary probability laws (including singular/discrete parts), Radon–Nikodym/density-ratio handling, and support-at-infinity conventions are not matched by the finite shared-base density results inspected.
- P2's exponential smoothing identity and converse density recovery require a dedicated formal statement with regularity hypotheses; the frozen source does not establish this.
- P4's one-dimensional Gaussian privacy-loss distribution calculation is absent as a direct Lean theorem in the frozen files.
- Centered Gaussian event bridge is formally covered in the one-way implication described above; exact extremal-event equality and endpoint sharpness remain outside that theorem's conclusion.

**Checkout inspection:** none beyond the frozen copies named in the manifest. **Effort:** approximately 4 minutes of source review; no compilation was run because the source types resolve the relevant scope question.
