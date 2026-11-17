# Hidden fixed-size f-DP subsampling: bounded consumer audit

## Reader question

Does the inspected formal development establish the source theorem `thm:subsample` for an arbitrary f-DP mechanism after hidden uniform m-of-n subsampling? The frozen reading, subsequent source clarification and exact application ledger are in [INTERPRETATION.md](INTERPRETATION.md) and [APPLICATION.md](APPLICATION.md). This is an informed development exercise using the previously exposed reserve.

## Verdict and reading

**Unresolved formal support for the complete mechanism claim.** No source mathematical fault was established. The manuscript's actual dataset definition, `fDP/fDP.tex:32`, defines same-size replace-one neighbors; `paper.tex:146` includes it. That resolves the reserve's prior adjacency uncertainty. Individuals are slots, including repeated record values, and sampled tuples must retain a consistent ordering.

The named formal `subsampleTradeoffAt` applies an operator to an existing curve. Its name does not establish a law for M composed with a sampler. `PrivacyObject.tradeoffAt ε` is itself a fixed-ε affine profile witness (`TradeoffFunction.lean:199–203`); identifying it with the source's entire hypothesis-testing trade-off is a further obligation.

## Decisive evidence

[Probe.lean](Probe.lean) checks two narrowly stated results: `surface_only` unfolds the actual definition; `operator_to_scalar` composes the curve comparison with the stronger appendix event-bound theorem in one consistent S, ε, δ context. [The final compiler receipt](attempt-final.json) has exit zero and only `propext`, `Classical.choice`, `Quot.sound`. The complete proposition and all five `ClassicalSubsamplingAppendixFeasible` constraints are printed in the receipt. This is ordinary Lean checking, not native completion/replay.

The scalar application still assumes a state S satisfying: the included/excluded alpha and beta decompositions, complementary excluded errors, and both included-error privacy inequalities. These are mathematically substantive premises. No proof here derives them from the arbitrary mechanism and the actual marginal output laws. The subset-replacement counting owner supplies a combinatorial inequality under pointwise bounds, not that missing probabilistic construction. Its Gaussian consumer also retains `hfeas`.

Alternative owners inspected: exact-surface equality transport compares existing objects; branch-tagged density pairs have output Bool×α and require a forgetting map; `OptimalSubsamplingLaw` constructs particular Gaussian mixtures. These are useful components, not the requested arbitrary-M application. Three inspected source modules lack direct compiled imports; this did not prevent the checked scalar route, and no compilation failure or source refutation is inferred. All negative statements concern these inspected routes, not global theorem absence.

## Original claims covered/unexamined

Covered: source adjacency clarification; exact sampler/output scope; actual operator definition; conditional classical scalar composition; precise premise boundary.

Unresolved: construct the normalized hidden output laws for arbitrary M, map original privacy assumptions and all tests to the LP constraints, and transfer both directed bounds to the source C_p conclusion. Unexamined: full validity/symmetry and biconjugate representation proof, appendix proof-method fidelity, tightness, Bernoulli extension and whole-paper correctness. No unperformed item is classified as an operational blocker.

## Remaining obligation

For each replace-one n-slot pair D,D′, construct L_D as the uniform mixture of M applied to the inherited-order restrictions over m-subsets. Under original f-DP of M on replace-one m-slot inputs, prove for every α∈[0,1] that C_(m/n)(f)(α)≤T(L_D,L_D′)(α). Repeat via the swapped ordered pair. The exact judgment and ledger are in APPLICATION.md. The present scalar result cannot close this judgment.

## What Ladon contributed

Local checkout Ladon 0.4.2 supplied one bounded owner search. Its stored response reports unchecked freshness and lexical fallback; it is navigation evidence only. The substantive boundary was determined by source/type inspection and ordinary Lean composition. No incremental detection or effort advantage, independent review, full import freshness, or fresh discovery is claimed.

## Recommended next action

Consolidate this as an exposed unresolved-support example for the existing complete-application recipe. A separately scoped MF mathematical follow-up could build the arbitrary-mechanism-to-testing-error adapter and conclusion conversion. No missing Ladon operation was reproduced, so this audit justifies no runtime diagnostic or automatic new campaign.

## Execution and evidence limits

The selected assessment finished before its 40-minute deadline with a precise unresolved route. It did not prove a global inability to complete the theorem. Two ordinary Lean attempts passed; the final recheck followed explicit binding of source/direct-import identities. No resource stop occurred. COSTS.json distinguishes logged checking from exploratory inspection. INPUT-VERIFICATION.json rechecks selected bytes; transitive compiled dependency closure is not certified. Source snapshots are retained under inputs/. Donor files/index/build state were not intentionally mutated. Original exposed evidence is untouched.
