# Plain reader report

The relevant lemma is `Mf.DP.fixedEpochCenterGap_pos_of_boundary_nonneg` in `Mf/DP/PoissonFixedEpochCenterGapPropagation.lean:430`. It requires a non-full point, positive `h`, `0 ≤ boundary < query`, and the additional premise `0 ≤ fixedEpochCenterGap point h boundary`; it then proves strict positivity at `query`.

Context A typechecks by applying that lemma directly. Context B omits the boundary-gap premise. The explicit Lean attempt stops at the obligation `0 ≤ fixedEpochCenterGap point h boundary`, so this is an unavailable prerequisite, not evidence the goal is false.

The exposition's all-horizon full-batch result is conditional on `a² ≤ (6E/(3E+2)) ε`; it compares full batch with every larger finite horizon and every nonnegative energy. It does not classify cases outside that condition or order all smaller batches. The formal strict-interior counterexample at `Δ=1, E=2, ε=1/4, δ=3/4` proves `v₃ ≤ 5/32 < 4/25 < v₂` and a strict total-variance reversal for `0 ≤ S ≤ 9/400`.

The sparse asymptotic concerns the complete released transcript for fixed clipped contributions with independent Poisson sampling and homogeneous independent Gaussian noise. It has the stated interior delta condition and a divergent transcript privacy variance. Average-only output has separate claims: its uniform bound and the average-only counterexample extension are conventional-only in the supplied assessments, not covered by the transcript targets. The exposition disclaims adaptive training-trajectory and training-loss conclusions, and fixed-rate asymptotics do not by themselves cover `q=E/T`.

The manifest contains no reviews. The guide/assessment records are model-attributed. The finite-map and stale-guide fixtures are explicitly synthetic: one highlights the extra `[Finite α]` premise (successor on `Nat` refutes the unrestricted statement); the other retains an approval attached to an older step revision after an edit. Neither is approval of this exposition.

Lean 4.33.0 elaborated context A using existing compiled artifacts. Context B failed on the missing premise. The first direct invocation lacked the Mathlib package path; adding the existing package library paths fixed imports. No Lake build, source mutation, or developer intervention occurred. Detailed conclusions and command evidence are in `reader-report.json` and `commands/`.
