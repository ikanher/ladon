# DP-SGD analytical GDP: bounded source-linked audit

The selected utility chain is supported by the inspected source and fresh local Lean checking. **No mathematical error was established in C1–C4.** The local convergence capsule was materialized; independent capsule replay did not complete. This is informed development work on the owner-nominated note, not a blind discovery test or a measurement of Ladon's comparative benefit.

## What the reader can conclude

The manuscript's finite expected-gradient bound applies to the stated Poisson-sampled, clipped Gaussian SGD recursion at any specified positive noise variance. Its Gaussian parameter must be interpreted consistently: multiplier standard deviation √V; post-normalization coordinate standard deviation C√V/(qN); total expected squared norm C²dV/(qN)². The stepsize multiplies the normalized noise afterward.

The chosen analytical GDP variance can be substituted exactly into that finite utility bound. The public upper bound F on the initial gap is retained, and no individual query potential is needed beyond a general objective with the stated mean-gradient relation. The capped square-root stepsize minimizes this bound and is admissible when its cap is no larger than the Poisson stability cap. These statements do not promise optimal observed training performance or finite privacy at the raw GDP variance.

## Scope and evidence

Primary source: [frozen manuscript](sources/latex/natural-language/dpsgd_analytic_gaussian_bound.tex), main theorem/corollary and GDP substitution, with utility proof. [First interpretations](FIRST-INTERPRETATIONS.md) were frozen before new checks. [INPUTS.json](INPUTS.json) binds the source snapshot, local Ladon runtime, toolchain, exposure and resource bounds. Source selection and source-reading preceded that freeze and are disclosed.

| Claim | Checked connection | Result and boundary |
| --- | --- | --- |
| C1: algorithm/noise units | `gdp_coordinate_law`, `arbitrary_variance_coordinate_law`, `arbitrary_variance_energy`; existing `gdpFormulaNoise_energy` | Coordinate-law and energy identities checked, beyond merely matching scalar second moments. Source inspection of Mechanism/Algorithm ties normalization and product history to the recursion. |
| C2: expected-gradient theorem | `public_gap_convergence` over existing `gaussian_convergence` | General f, measurable queries, mean-gradient identity, smoothness, variance, lower bound and Poisson step restriction retained. Public F>=actual gap checked. Pre-update average, not final-iterate gradient. This arbitrary-positive-variance route is the faithful control for specialization. |
| C3: optimal learning rate | `physical_optimizer`, `optimal_step_admissible`; existing `optimalStep_pos`, `optimalStep_le_cap` | Same D coefficient; positive F,T,L,W and cap; cap<=stability cap. Optimality and admissibility are separate checked statements, composed by the stated parameter mapping. |
| C4: GDP substitution | `general_objective_gdp_convergence`, `gdp_coefficient` | General objective/public F retained. Literal logarithmic coefficient checked. The formal raw expression accepts q=1; its interpretation as the manuscript's subsampled prescription is restricted to 0<q<1. |
| C5: fixed-update batch comparison | Existing `gdpUpper_retuned_antitone_batch` type/axioms inspected | Partial: raw-formula theorem available; no new bridge to the distinct q=1 prescription checked. Not a completed comparison audit. |
| C6 and remaining paper | Inventory only | Exact-pass comparisons, asymptotics, Gaussian-profile inversion, privacy appendices, finite corrections/counterexamples and numerical tables remain unexamined here. Abadi/Bu literature assertions were not independently verified. |

[Audit.lean](Audit.lean) contains eight small checking adapters; it does not change production mathematics or Ladon. Existing proof owners were inspected for the algorithm and convergence route, rather than accepting an arbitrary implication or the finite-sum application as the full prose statement. In particular, the stronger per-query-potential assumptions of `finite_sum_gdp_formula_convergence` were avoided by using `gaussian_convergence` directly. That navigation distinction is resolved support, not an exposition bug.

## Verification and resource observations

- [lean-01.json](lean-01.json): first five adapters passed; original source retained as Audit-v1.lean with its hash in lean-01-source.json.
- [lean-02.json](lean-02.json): final eight adapters passed, plus five existing owner interfaces checked. All 13 axiom reports contain only `propext`, `Classical.choice`, `Quot.sound`; no sorry axiom appears. Final pass: 3.194 seconds, peak aggregate process-tree RSS 7,660,314,624 bytes (about 7.13 GiB).
- [dependency-preflight.json](dependency-preflight.json): `lake --no-build build Mf.Optimization.PoissonClippedSGD.GDPApplications` succeeded; all 8,744 jobs reported up to date. It did not rebuild 8,744 modules. The local checks use these compiled imports and the pinned Lean 4.33.0 environment.
- [navigation.json](navigation.json): local-checkout Ladon found the exact theorem with verified-fresh lexical indexing. Lexical navigation is not a proof dependency claim.
- [FINAL-VERIFICATION.json](FINAL-VERIFICATION.json): all frozen source files and local Ladon runtime files unchanged; final Lean source and first-interpretation digests recorded; axiom allowlist checked.
- [REVIEW.md](REVIEW.md): independent Luna-medium review upheld C1–C4 within these limits after correcting initial reviewer errors and checking the cap bridge.

These are bounded local checks, not independent reconstruction of all dependencies. Memory was capped at 12 GiB per process tree; no exhaustion occurred. Two Lean passes total about 6.9 seconds; dependency preflight took 4.5 seconds and indexed navigation 6.4 seconds. Source preparation, capsule extraction, reasoning and review costs are not fully instrumented; token/human-effort accounting is unavailable. These numbers cannot support an efficiency comparison.

## Local capsule

[convergence-capsule/capsule.json](convergence-capsule/capsule.json) packages `Mf.Optimization.PoissonClippedSGD.gaussian_convergence`, with 177 repository semantic nodes and 27 planned source modules. The capsule directory is about 10.5 MiB. It binds the existing general convergence theorem, not every adapter in this audit or the whole paper.

[Extraction](capsule-extract.json) succeeded with status `materialized_unverified`. [Replay](capsule-replay.json) returned `unsupported-facet`: the fresh sanitized copy lacked Mathlib, and network-denied acquisition could not fetch it. This is a dependency-readiness failure before proof comparison, not a Lean refutation. No unrestricted fallback or higher-memory retry ran. The capsule is locked/rebuildable with external dependency frontiers; it is not an offline-vendored artifact. Independent replay remains explicitly unresolved.

## What this teaches Ladon development

Existing Ladon navigation/capsule commands and ordinary Lean sufficed to construct reviewable local evidence. The exercise did not demonstrate a missing mathematical diagnostic, a newly found fault, or an advantage over competent ordinary Lean work. The meaningful work was selecting the correct general theorem, preserving public tuning assumptions, checking physical noise units, and connecting scalar optimality to an admissible actual run.

Do not integrate three new diagnostics on the strength of this successful support check. The next choices are to supply dependency artifacts for independent capsule replay, or audit the remaining batch-comparison/endpoint claims as a separately scoped extension. A fresh comparative pilot still needs declared success criteria, equivalent ordinary-Lean recipes, fresh inputs and full cost accounting.
