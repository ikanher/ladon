# Independent plain-reader report (r49)

## Claim and limitations

The authored guide, component assessment, canonical manifest, and exposition attachment support this summary. The fixed-epoch all-horizons corollary gives a sufficient condition: for integer E>0, T>E, Δ>0, ε>0, and 0<δ<1, if a=Δ/√v_FB obeys a² ≤ 6Eε/(3E+2), then v_FB < v̄_(E,T) ≤ v_(E,T) and, for every S≥0, V_E(E,S)=V̄_E(E,S)<V̄_E(T,S)≤V_E(T,S). It is not a classification beyond that parameter domain and does not rank all pairs of smaller batches.

The release scope is independent Poisson sampling of fixed clipped contributions, homogeneous independent Gaussian noise, and equal-weight averaging. The sparse theorem is about the complete transcript. Average-only output has a separate uniform feasibility bound; the corresponding strengthening in the all-horizons corollary is marked conventional-only, so transcript targets do not establish the average-only claim. The manuscript excludes adaptive optimizer trajectories and training loss. Its sparse limit fixes E, Δ, ε, δ, assumes 0<δ<1−e^(−E), and does not derive the fixed-rate result at q=E/T without uniformity in q. A positive-noise counterexample (E=2, ε=1/4, δ=3/4) gives v₃≤5/32<4/25<v₂ and V₂(3,S)<V₂(2,S) for 0≤S≤9/400; unconditional full-batch optimality is false.

## Supporting lemma and the two contexts

I independently selected `fixedEpochCenterGap_pos_of_boundary_nonneg` in `Mf/DP/PoissonFixedEpochCenterGapPropagation.lean`. For a non-full point and positive scale, it requires a nonnegative boundary, boundary<query, and the substantive premise 0≤fixedEpochCenterGap point h boundary; it concludes strict positivity at query. Its proof uses strict convexity of the exponential tilt, its strict deficit at zero, a positive Gaussian density factor, exact differentiation of the gap, and the gap tending to zero at +∞.

Context A includes the boundary-gap premise. A standalone Lean 4.33 check succeeded through the repository existing Lake environment (`compile-context-a2`). Context B omits that premise. Its standalone application failed with a residual function requiring 0≤fixedEpochCenterGap point h boundary (`compile-context-b`). This is an application-shape/premise failure, not evidence that the theorem is false. The first direct invocation supplied only the root build directory and failed to find Mathlib (`compile-context-a`); `lake env lean` corrected the import path. No source or shared build files changed.

## Formal coverage and review currency

The manifest and guide say transcript privacy and total-variance finite-horizon conclusions and the full-batch reference have formal target bindings. Of 26 component assessments, 15 are labelled source-correspondence, 9 conventional-only, and 2 reported-implication-without-checked-adapter. The average-only all-horizons strengthening is conventional-only; the sparse theorem offset and leading asymptotic adapters are reported implications without checked adapters. These labels describe coverage, not independent mathematical certification. The assessment basis says it is model-attributed correspondence rather than independent certification. Both real manifest and guide have empty review arrays, so I found no current real reviewer approval in this bundle.

The separate finite-map fixture makes the mismatch concrete: its informal claim says every injective self-map is surjective, while its Lean type additionally assumes `[Finite α]`. Its digests and project revision are explicitly illustrative. The stale-guide fixture has an approved review pointing to the previous explanation revision, while the edited explanation has a different revision; it also identifies the reviewer as a synthetic tool observer. Neither fixture is a real review or approval of this exposition.

## Retained evidence

Command records are in `/home/codex/.cache/ladon-reader-loop-r49/plain-retest/commands/`. Relevant labels: `task-environment`, `read-guide-assessment`, `manifest-map`, `inspect-lean-source`, `exposition-scope-proof`, `inspect-synthetics-claims`, `compile-context-a2`, and `compile-context-b`. Candidate sources are frozen read-only project files; my applications are `/home/codex/.cache/ladon-reader-loop-r49/plain-retest/context-a.lean` and `context-b.lean`.
