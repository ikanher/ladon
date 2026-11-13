# First source interpretation

Source: `../lean/matrix-factorization/paper/theory/mu-dp/subsample.tex`, SHA-256 `11223a25e22c97b4c57dd08fd231d53da8c1664430c40cecb97a8c0e6eb561bb`. This is the tracked current local source. The present root auditor read the selected source before inspecting any candidate formal declaration. The earlier C05 inventory had already exposed the existence of a convexified operator and an unresolved law-realization map; this is an informed follow-up, not a held-out detection run.

## Selected claim and required mapping

The source defines `Sample_m(S)` as a **uniform random subset of exactly `m` indices** of a public `n`-slot dataset, with `1 ≤ m ≤ n`. `M` acts on the resulting `m`-record dataset. The intermediate subset is hidden; the released mechanism is only `M(Sample_m(S))`. The source theorem says: if `M` is `f`-DP on `X^m`, then this hidden fixed-size subsampled mechanism is `C_p(f)`-DP on `X^n`, for `p=m/n` and `C_p(f)=min{f_p,f_p^{-1}}^{**}`, `f_p = p f + (1-p) Id`, `Id(x)=1-x`.

The theorem would need more than an operator identity. A formal counterpart must identify the input adjacency relation on size-`m` and size-`n` datasets, a uniform `m`-subset law, the input-to-selected-dataset map, the private `M` kernel and its `f`-DP assumption, hiding of the sampled indices, the resulting output law, and the trade-off lower bound by `C_p(f)` in both neighboring directions. The theorem statement in this section leaves the precise adjacency definition to surrounding paper context; that remains an interpretation question, not an inferred premise.

The displayed proof route converts `f`-DP to a family of approximate-DP statements, applies a classical fixed-size subsampling theorem, then converts back through the asymmetric `f_p` and symmetrized convex envelope. The source explicitly treats independent Bernoulli sampling as an additional scheme whose analogous theorem follows from a corresponding classical result. I will keep that separate from the stated fixed-size `Sample_m` theorem.

The immediate reader question is whether the available Lean operator is connected to the **same hidden fixed-size mechanism output law**. A theorem about `C_p` alone, or about a Bernoulli sampler, would not establish this source theorem. A missing formal bridge would be an unresolved support boundary, not by itself a mathematical counterexample to the paper.
