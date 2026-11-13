# First interpretation, before formal-owner inspection

Source: `../lean/matrix-factorization/latex/natural-language/poisson_gaussian_rational_calibration.tex`, current local bytes SHA-256 `05323bd393fe2dce1a5be9f4605717bbcf826b06e7565f1f8324f1a8ceb81aaf`. This file is currently untracked in the sibling repository, so this exercise binds its bytes rather than a commit. The present root auditor has seen the source text and only the names of two possible Lean counterparts; prior audit/result JSON files were not opened. This is an exposed, author-run audit, not a fresh or independent discovery score.

Selected passage: the theorem **“Soundness and eventual acceptance”** and its immediately preceding definitions. The source fixes integers `T ≥ 1`, `m ≥ 2`, rational `ε > 0`, `0 < δ < 1`, `0 < q < 1`, and `σ > 0`. It chooses rational exponential lower/upper bounds at precision `N ≥ 1`, with range-reduction powers fixed as `N` varies. It defines `B_N` from upper bounds on each mixture term and `D_N = δ L_N(E)`, where `E = (m-1) ε`.

The theorem has two claims:

1. If the exact rational test `B_N^T ≤ D_N` succeeds at any precision, the specified adaptive Poisson-sampled Gaussian mechanism is `(ε, δ)`-DP in both adjacency directions, with an independent public seed and common randomized postprocessing as described above the theorem.
2. If the real moment condition is strict, `A^T < δ exp(E)`, then the rational test succeeds at every sufficiently large precision. This is an eventual-acceptance claim, not a guarantee for arbitrary fixed noise at the equality boundary.

The source's proof of the first part uses nonnegative weights and termwise exponential bounds to obtain `A^T ≤ B_N^T ≤ δ L_N(E) ≤ δ exp(E)`, then invokes a companion exact-moment-to-privacy result. The second part uses convergence of the rational endpoints and positive gap. The formal counterpart must preserve the order, power `T`, both directed privacy comparisons, and the mechanism/seed/postprocessing map. It may split the scalar certificate and mechanism conclusion across declarations. A scalar inequality alone would not certify the full theorem. The actual Lean objects and their support remain to be inspected.
