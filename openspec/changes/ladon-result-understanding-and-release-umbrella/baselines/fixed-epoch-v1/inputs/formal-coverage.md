# Statement-level formalization coverage

This is the current manuscript's coverage addendum. It supersedes historical
coverage prose for interpretation of the article, without changing the pinned
Lean sources. The publication distributes this file as `formal_coverage.md`.

The formal reference is **source supplement r05**, archive SHA-256
`f8e2839b485b073353df435dd3a9ea3f7d53abb48b14b99f55f3238e0096327b`.
Its source identifier is
`4361250dba7bdeb659c95ecfdd88170ee0c1f36339feb7535e59609966f8f083`;
the archive README defines the serialization that this identifier hashes.
The archive includes all project-local imports and root Lake metadata for its
replay targets. Pinned external packages must still be available.

All declaration names below are in namespace `Mf.DP`; module paths are under
`Mf/DP/` **inside r05**. Coverage refers to exact statements and hypotheses,
not to whether the article follows the same proof strategy. No current
working-tree facade or later result is silently substituted for r05.

## 1. Finite comparisons

Write `a=Delta/sqrt(v_FB)`. Unless a row fixes numerical values, the finite
dominance hypotheses are positive integers `E,T` with `T>E`, `Delta>0`,
`epsilon>0`, and `0<delta<1`. Total-variance comparisons assume `S>=0`.
The formal comparisons in this section use **transcript calibration**.

| Article claim (LaTeX label) | r05 declaration and module | Exact coverage |
| --- | --- | --- |
| All-horizon dominance (`cor:fixed-epoch-all-horizon`), transcript conclusion | `poissonFixedEpochCalibratedPrivacyVariance_gt_fullBatch_of_epochUniformSignal`; `poissonFixedEpochTotalAverageVariance_fullBatch_lt_allEnergy_of_epochUniformSignal`, in `PoissonFixedEpochEpochUniformDomain.lean` | Closed condition `a^2 <= 6E*epsilon/(3E+2)`; every finite `T>E`; all nonnegative energies |
| Equivalent privacy-target condition | `poissonFixedEpoch_allHorizon_dominance_of_delta_le_epochUniformThreshold`, same module | Quantified conclusion under the equivalent Gaussian-profile threshold; exact conditions, not a grid check |
| Horizon-dependent dominance (`thm:rate-adaptive-pointwise`), transcript conclusion | `poissonFixedEpochCalibratedPrivacyVariance_gt_fullBatch_of_exactCriticalSignalSquareCondition`; `poissonFixedEpochTotalAverageVariance_fullBatch_lt_of_exactCriticalSignalSquareCondition`, in `PoissonFixedEpochPointwiseDominanceDomain.lean` | Closed `a^2 <= Lambda(E,T)*epsilon` except at `T=2E`, where the formal condition is strict; the article's equality endpoint is a conventional addition |
| Secant criterion (`thm:support-width-accountant`), transcript conclusion | `poissonFixedEpochCalibratedPrivacyVariance_gt_fullBatch_of_supportWidth`; `poissonFixedEpochTotalAverageVariance_fullBatch_lt_allEnergy_of_supportWidth`, in `PoissonFixedEpochNearFullDominance.lean` | Dedicated theorem uses `a^2 < 2*epsilon*E/(T-1)`; its epsilon hypothesis allows zero, where this strict condition is empty |
| Positive-noise reversal (`thm:strict-interior-counterexample`) | `strictInterior_calibratedPrivacyVariance_le_five_thirty_seconds`; `strictInterior_calibratedPrivacyVariance_lt_adjacentFullBatch`; `strictInterior_totalVariance_lt_fullBatch_of_energy_le_nine_four_hundred`, in `PoissonFixedEpochStrictInteriorCounterexample.lean`, with `PoissonFixedEpochFullBatchFourTwentyFifthsBracket.lean` | `Delta=1,E=2,T=3,epsilon=1/4,delta=3/4`; sampled variance at most `5/32`, full-batch lower bracket `4/25`, and inclusive energy interval `0<=S<=9/400` |

The factor identities and the strict comparison of each finite coefficient
with the uniform coefficient are proved in
`PoissonFixedEpochSkewBoundarySignalAlgebra.lean`.

### Full-batch comparator and infima

Some privacy-variance statements write the left side as the square of
`fullBatchGaussianBaseStddev`, rather than the calibrated infimum at `T=E`.
The identification is proved by
`poissonFixedEpochPrivacyVariance_fullBatch_eq_base_sq` in
`PoissonFixedEpochVariance.lean`, under `E>0`, `Delta>0`, `epsilon>=0`,
`0<delta<1`. Thus this is the article's `v_FB`, not an alternative comparator.

The formal finite lower-bound proofs do not assume the article's general
attainment lemma. They establish a strict profile/event margin near the
full-batch candidate and use proved feasibility, monotonicity and infimum
bounds. Counterexample upper bounds supply an explicit feasible noise.

### Secant equality points

At equality in the article's secant condition, all cases other than `E=1,T=2`
lie within the formal horizon-dependent domain: for `E<T<2E` its coefficient
is at most 2; for `T=2E,E>1` it is strictly below 2; for `T>2E` it is at most
1 and strictly below the rate-adaptive coefficient. This is a mathematical
implication of the formal theorem's hypotheses, not a claim that r05 packages
a separate closed-secant corollary. The remaining corner and the pointwise
symmetric endpoint are proved by the article's average-threshold argument.

## 2. Sparse limits

These statements concern the canonical **transcript** profile. The general
schedule is `FixedParticipationSchedule`: rates in `[0,1]`, a positive limiting
participation budget `rho`, and `T*q_T -> rho`.

| Article claim (LaTeX label) | r05 declaration and module | Hypotheses and translation |
| --- | --- | --- |
| Critical-window profile (`thm:accountant-limit`) | `tendsto_sampledGaussianProductProfileStddev_finiteOffset` in `FixedParticipationGaussianAccounting.lean` | `Delta>0`, fixed `epsilon>=0`, eventually positive noise, and `Delta/sigma_T - sqrt(2 log T) -> s`; limit is `1-exp(-rho*Phi(s))`, represented by `ENNReal.ofReal` |
| Calibrated offset (`thm:fixed-participation-calibration`) | `tendsto_fixedParticipationCalibratedStddev_offset` in `FixedParticipationGaussianCalibrationAsymptotics.lean` | `Delta>0`, `epsilon>=0`, `0<delta<1-exp(-rho)`; offset is the Gaussian quantile of `-log(1-delta)/rho` |
| Fixed-E raw-noise equivalent and vanishing (`thm:smallbatch`) | `tendsto_poissonFixedEpochCalibratedStddev_smallRate_ratio_one`; `tendsto_poissonFixedEpochCalibratedStddev_zero`, in `PoissonFixedEpochAsymptotics.lean` | Positive integer E, `Delta>0`, `epsilon>=0`, strict subcritical delta; horizons parameterized as `E+extra` |
| Fixed-E privacy-variance equivalent and divergence (`thm:smallbatch`) | `tendsto_poissonFixedEpochPrivacyVariance_div_leadingTerm_one`; `tendsto_poissonFixedEpochPrivacyVariance_atTop`, same module | Leading term `Delta^2/(2*E*q*log(1/q))`; same strict subcritical hypotheses |
| Fixed-energy total-variance equivalent (`eq:total-equivalent`) | `tendsto_poissonFixedEpochTotalAverageVariance_div_leadingTerm_one`, same module | Same hypotheses and fixed nonnegative energy |
| Uniform eventual total-variance dominance (`cor:eventual`) | `eventually_poissonFixedEpoch_fullBatch_lt_totalAverageVariance_uniform_energy`, same module | One eventual horizon cutoff works for every nonnegative energy |

The fixed-E offset in the article is obtained from the general calibrated-offset
statement by the capped schedule `q_T=min(1,E/T)`, equal to `E/T` for admissible
horizons. No separate packaged Lean theorem for that precise fixed-E offset
specialization is claimed. The general offset already uses `sqrt(2 log T)`.

The fixed-E **leading equivalents** in the formal source use `log(1/q)`.
For `q=E/T`, this is `log(T/E)`; at fixed E its ratio to `log T` tends to one.
This elementary conversion gives the article's leading equivalents. It does not change the
constant-order offset or justify substituting a vanishing q in a fixed-rate
limit. The formal profile is ENNReal-valued; its finite limit corresponds to
the real-valued profile in the article.

## 3. Conventional-only additions

No formal-verification claim is made here for these exact article statements:

- the definition and calibration theorems for the canonical average alone,
  its finite strict-dominance conclusions, total-variance comparisons, uniform
  feasibility bound, or transfer of the counterexample;
- the pointwise symmetric endpoint `T=2E, a^2=2*epsilon`, including the
  `E=1,T=2` secant corner;
- continuity at zero and attainment for the general finite calibration
  infimum in `lem:calibration`;
- the fixed-query domination channels in `app:canonical-domination`;
- the article's alternative elementary maximum-event proof of divergence
  as a particular proof strategy (the divergence conclusion is formal above).

These are conventional proofs in the article, not open mathematical obligations.
The inventory makes no claim that no related result exists elsewhere in the
repository. The current endpoint proof improves an event of the average; the
older r05 coverage prose describes the earlier transcript argument.

## 4. Replay and evidence provenance

The r05 README gives the exact three build targets and direct Lean commands.
Its integrity-only verifier checks source hashes, the project-local import
closure, and finite table consistency; it does not run Lean. Use an isolated
extraction with pinned dependencies for a fresh replay.

Claude's independent review on September 30, 2026 reports a successful isolated
replay of all 235 local modules: exit 0, 11 minutes 42 seconds. The supplied
`lean-replay.log` records that exit and standard axiom reports. Its additional
`ReviewExtraAxioms.lean` explicitly checks the two sparse endpoints omitted
from the original audit's printed axiom list. The supplied extra log lists only
`propext`, `Classical.choice`, and `Quot.sound` for both. This revision inspected
those source statements and logs; it does not relabel the external replay as a
new Codex build.

The current source package includes `SparseCoverageAudit.lean`, the two sparse
`#check`/`#print axioms` pairs, for reproducible additional auditing. From an
isolated built r05 extraction, copy that file to the extraction root and run
`lake env lean SparseCoverageAudit.lean`. No theorem owner or r05 archive byte
has changed. Additional query coverage is not an extension of theorem scope.

The article's finite reversal is backed by the semantic enclosure-to-accountant
chain in r05. By contrast, the larger parameter-sweep figures use numerical
calibration with diagnostics, not rigorous error enclosures or Lean certificates.
