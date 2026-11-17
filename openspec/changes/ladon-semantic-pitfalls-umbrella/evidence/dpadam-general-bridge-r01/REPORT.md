# General fixed-query and initialization bridge

U.5 continuation, informed root work, 2026-11-14. This is a local mathematical composition using existing compiled donor imports. The original r01 investigation and its premature all-blocked terminal remain preserved. This continuation does not replace that terminal, restart its clock, or claim completion of its source inventory.

## Checked result

`Bridge.lean` compiles in pinned Lean 4.33.0 and prints only `propext`, `Classical.choice`, and `Quot.sound` for every reported declaration. Three successive drafts passed. Receipts retain commands, source hashes, sampled RSS and timing. The final check took 2.72 seconds with peak sampled RSS 7,407,919,104 bytes, within the 60-second/12-GiB process bounds. These are ordinary Lean checks; no new native completion/replay or portable dependency closure is claimed.

- `fixed_query_local_mean` proves the exact local-mean premise in arbitrary finite universe/dimension, from row queries equal to one fixed query. It uses the data's existing clipping/dataset equalities and zero approximation error. It requires neither centered quadratic queries nor an assumed limiting mean.
- `withInitial` and `withPublicInitial` construct row families with constant within-row initial points x_j. Their nested mesh initialization and fluctuation premises hold identically, and `public_initial_coherence` follows solely from x_j tending to x0. No extra rate is imposed on that public sequence.
- `public_initial_clock` proves the transformation preserves clock and learning rate.
- `fixed_query_public_initial_limit` applies the actual named-covariance path-law theorem to the transformed data. Its conclusion displays the Gaussian driver pushed through the nonlinear solution map, with the empirical clipped mean of the fixed queries and initial point x0. The theorem discharges mean and initialization premises rather than supplying the desired law as a hypothesis.

## Source mapping and remaining obligation

The source fixes the queries across runs and assumes x_j tends to x0. Those two source conditions can therefore supply the corresponding consumer premises without the quadratic restriction. `GrowingClockData` itself permits row-varying query functions, so the fixed-query equality must still be established by the constructor/object map; it is not automatic from the record type.

The named-definition screen retained five constructors: quadratic/exact-count and zero-query examples (including calibrated wrappers). This is a scoped lexical inventory, not proof that a general producer is absent throughout the repository. The inspected exact-count `supplied_clock_eq` and `supplied_exact_products` consume actual family records rather than constructing arbitrary query families.

The remaining original obligation is to construct the two actual family records from the general source primitives at q and kq, supplying each actual release-kernel measurability and recordwise query regularity field, public normalization B=qN, and exact count/noise/horizon equalities. The objective field also has a `SmoothObjective` interface with a two-sided Taylor remainder; the source's globally Lipschitz record gradients may justify this, but that adapter must be derived and bound to the empirical objective rather than assumed. The utility consumer separately requires its f/gradient/Hessian/dispersion mapping. Neither the existence of an input `GrowingClockData` nor a clean axiom report supplies these missing constructions.

This is unfinished mathematical work, not an evidenced inability to continue and not a Ladon runtime failure. U.5 remains open. Its next step is the general source-to-family constructor/objective mapping, followed by joining the two named laws and the privacy/finite-iterate utility consumers. Reusing another quadratic example would not discharge that step. No production feature or broader comparison is proposed by this result.
