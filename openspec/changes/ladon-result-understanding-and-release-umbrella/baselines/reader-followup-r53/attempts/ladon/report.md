# Independent reader report: alpha-loop / fixed-center gap

## Finding

The supplied full-batch optimality statement is conditional and scoped. The guide's authored summary says that for integers E>0 and T>E, sensitivity Δ>0, ε>0 and 0<δ<1, with a=Δ/√v_FB, the sufficient condition a² ≤ (6E/(3E+2))ε yields v_FB < v̄_(E,T) ≤ v_(E,T), and strict full-batch total-variance dominance for every S≥0. It expressly does not classify the outside domain or order every pair of smaller batches. This is an authored guide claim; the guide marks proof coverage unknown and says it does not run checks. The claim inventory says it covers theorem/lemma/proposition/corollary environments, not every equation, definition, or proof step.

A relevant lemma for the assigned Lean goal is `Mf.DP.fixedEpochCenterGap_pos_of_boundary_nonneg` in `Mf/DP/PoissonFixedEpochCenterGapPropagation.lean`. Its premises, in order, are a point, h, boundary, query, `point.epoch < point.horizon`, `0 < h`, `0 ≤ boundary`, `boundary < query`, and `0 ≤ fixedEpochCenterGap point h boundary`. It concludes `0 < fixedEpochCenterGap point h query`. The proof's mechanism is the positive-factor derivative formula with an exponential tilt: strict convexity and tilt(0)<1 control the derivative until the tilt crosses one; after crossing, the gap decreases strictly and tends to zero, so it remains strictly positive. This supports context A exactly. Context B lacks the boundary-gap premise. The candidate checker returned `applicable-with-residuals` with residual `?hBoundaryGap`; therefore B is not completed by this lemma. This is an unmet premise, not evidence the goal is false.

## Direct application observations

I submitted the pinned declaration candidate against each task-provided closed goal, preserving its binder order, with explicit Lean 4.33.0 executable paths and the supplied source module. Context A was accepted by the elaborator with no residuals. Context B was applicable only with residual `?hBoundaryGap`. The first attempted command passed an application term where the CLI requires a declaration name and failed with `invalid-invocation`; I retained that attempt and reran with the declaration name. A separate first attempt to locate the recorder used a nonexistent path; it did not inspect task data. One initial guide CLI call was mistakenly run outside the recorder; it produced the same qualitative guide findings as the recorded guide call, but is not treated as recorded evidence. No source edits, builds, or manual database/cache changes were made.

## Release scope, evidence, and review currency

The real supplied inspection reported 25 resolved canonical targets and 26 authored component assessments. Those assessments are model-attributed, not independent certification. The assessments distinguish conventional-only items from source-correspondence items; for example, average-only extensions are conventional exposition, while the full-batch target has a stored exact type/source binding. Such bindings establish navigation to supplied declarations, not informal equivalence or proof coverage. The real review section contained zero review rows. The guide's attribution/currency labels and the stored operations are metadata and must not be read as independent approval. The checking section contains stored elaborator observations, but inspection of those records does not execute them; my two candidate checks above are fresh observations limited to the exact supplied goal, module, and pinned environment. Source freshness remains unknown.

The finite-map fixture illustrates an additional premise: the formal type requires `[Finite α]` while its informal statement is unrestricted, so it is not a real assessment of this exposition. The stale-guide fixture keeps an approval pointing at the prior explanation revision after the explanation changes; the changed guide has no review. Both fixture reviews/source identities are explicitly illustrative and neither constitutes real approval.

## Limits

I did not establish that the full-batch result is false outside its sufficient domain, nor prove a stronger average-only claim. Context B remains unresolved: another independent premise or a different proof is needed. The accepted context-A check is a fresh exact elaborator observation, not an independent human review and not a source-freshness guarantee.

## Retained evidence

Recorded command/output files are under `/home/codex/.cache/ladon-reader-followup-r53/ladon/commands/`. Key records: `guide-steps`, `supplied-lemma-source`, `synthetic-evidence`, `real-assessment-inspect`, `real-review-inspect`, `real-check-inspect`, `context-a-declaration-candidate`, and `context-b-declaration-candidate`. Total recorder-accepted task commands: 22 of 24. One unrecorded initial guide call and two failed setup/invocation attempts are disclosed above.
