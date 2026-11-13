# Evidence collected before independent review

Input authority: `inputs/MANIFEST.json`, verified after copy (15/15 SHA-256 matches; frozen source files are clean in the target checkout). First interpretations: `INVENTORY.md`, SHA-256 `e22601ec6322fe149824095ad6bf73c28251c8f2fa45111bdec7706fe9fa9743`.

## Fresh local Lean check

At 2026-11-12, from the frozen math checkout (`f5b46eeee13e8f9d3cf161627c213a130241c593`, Lean `leanprover/lean4:v4.33.0`), ran:

```bash
timeout 300 lake env lean ../ladon/openspec/changes/ladon-pld-core-source-audit/evidence/pld-core-r01/work/AuditCheck.lean
```

Exit code 0. The scratch file imports the selected owners and asks Lean for exact signatures and `#print axioms` of:

- `Mf.DP.privacyLossSet_bound_iff_dp_event_bound`
- `Mf.DP.expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local`
- `Mf.DP.PLDPair.comp`
- `Mf.DP.concretePLDPair_sharedBaseProduct_eq_compFamily`
- `Mf.DP.analyticGaussianCondition_iff_event_form`

The source, command and full output are preserved at `inputs/` and `work/AuditCheck.lean`, `work/audit-check.log`. This typechecks a scratch import/check file against existing compiled imports. It is not a rebuild of the selected owners or an isolated capsule replay. All three inspected theorem axiom reports show `[propext, Classical.choice, Quot.sound]`; this is a trust report, not source correspondence evidence.

## Claim-linked observations

| Claim | Observed formal evidence | First disposition before reviewer |
|---|---|---|
| P2: likelihood-ratio law and event profile | The event core gives an iff between a positive-region integral bound and all measurable event inequalities, under measurability/integrability. The density-to-loss identity is stated for a shared base measure with both densities pointwise strictly positive, and identifies a mapped loss law's hockey-stick functional with a source-space integral gap. | Partial support for event/profile algebra on the formal theorem's exact domain. No evidence yet that this covers arbitrary laws, zeros/singular mass, the paper's generalized PRV definition, or every step in the appendix proof. No discrepancy established. |
| P4: independent composition | `concretePLDPair_sharedBaseProduct_eq_compFamily` gives exact equality for finite heterogeneous products over one shared base, with measurable, nonnegative and strictly positive coordinate densities plus finite-measure instances. `PLDPair.comp` is an abstract pair-of-measures construction by mapped sums. | Strong formal support for this exact product-density case. The broader source theorem about privacy curves is not established merely by this theorem name; map its definitions and independence conditions before accepting full correspondence. No discrepancy established. |
| G1/G2: Gaussian control candidate | Lean checks the explicit standard-Gaussian event formula, its Gaussian-real form for positive `σ`, and `gaussianPair_eventApproxDP_centered_of_analyticCondition_lt_one`. The last theorem states that, given `0 < σ`, `0 ≤ ε`, `0 ≤ Δ`, squared distance at most `(Δ/2)^2`, the analytic condition, and `δ < 1`, every measurable event satisfies the directed centered Gaussian approximate-DP inequality for means `d` and `-d`. | Supported as the one-way scalar-condition-to-all-events bridge under those exact assumptions. It does not establish the note's maximizing half-space equality, endpoint sharpness, radial identity/envelope, or the Gaussian PRV law. Independent review confirms this boundary. |
| P1/P3 | No fresh goal was checked for general PRV definition, converse derivative reconstruction, differentiability or uniqueness. | Unresolved/not checked; outside the selected local support result. |

Search evidence used the local Ladon index at generation `046b95eaf8b8ab773fdfb6dc9927ed3dfa556664f32878cb43d8e526d3c9d7bf`, freshness `fresh` at status capture, evidence mode `lexical-fallback`, 267,424 declaration rows, 1,809 omissions. Searches are navigation only. The selected theorem signatures were verified by Lean above. No compiled lineage, fresh owner rebuild or whole import-closure replay was performed.

## Limits

The compile check does not prove the paper's mathematical correspondence by itself. Density positivity excludes zeros and singular components from the direct bridge. The exact product equality covers a specified finite product model; a privacy-curve composition claim requires matching the source's `⊗` and probability-law semantics. The Gaussian one-way control is supported, while the maximizing-event/radial equality and endpoint sharpness remain outside the checked theorem. No mathematical error is established by this evidence.

## Independent-review reconciliation

The source-only reviewer independently confirmed the central scope boundaries. In particular, the paper's P2 converse density recovery is a density-level claim requiring smoothness and tail/density regularity; the frozen Lean owners contain event/profile and positive shared-density bridges, but not the exponential-smoothing identity or converse `δ''−δ'` recovery theorem. The review classifies this as a formalization/scope gap, not an established fault. For P4, the checked finite shared-base product theorem does not directly establish the paper's Gaussian privacy-loss laws or general PRV composition. The Gaussian event implication is a justified control only in the one-way direction and with the premises listed above. See `review/REVIEW.md` and `RECONCILIATION.md`.
