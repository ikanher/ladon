# Selected application and remaining obligations

Exact source judgment: for n,m with 1≤m≤n, arbitrary data domain X and output space Y, probability kernel M on ordered m-slot datasets, f a valid trade-off lower bound for M on replace-one neighbors, prove that for every replace-one n-slot pair D,D′ and test level α∈[0,1], C_(m/n)(f)(α) ≤ T(L_D,L_D′)(α), with L_D the uniform average of M(D restricted to I) over m-subsets I⊆Fin n, selected slots enumerated in their inherited order. The reverse direction follows by quantifying ordered neighboring pairs. No sampled identities are released.

| Obligation | Source basis | Producer/check | Status | Residual |
| --- | --- | --- | --- | --- |
| Replace-one adjacency | fDP/fDP.tex:32, included by paper.tex:146 | surrounding source inspection | attributed | Lean data/adjacency map |
| Uniform exact-count law on slots | subsample.tex:37 | sizeMSubsets, subset replacement counting | attributed | probability-normalized output-law constructor for arbitrary M |
| C_p operator expression | subsample.tex:44–49 | pSamplingOperator definition | attributed | paper biconjugate/convex-envelope identification under valid f, restricted domain |
| Operator only, not new law | formal definition | Probe.surface_only | checked (`attempt-final.json`) | no output-law conclusion follows from definitional equality |
| Classical scalar LP endpoint | appendix route | Probe.operator_to_scalar, conditional on all LP feasibility constraints | checked (`attempt-final.json`) | construct S and prove feasibility from original M, sampler and a test |
| Actual marginal law testing bound | source theorem | inspected owners | unresolved | connect both output laws and all tests to the LP state and then convert event bounds to C_p |
| Symmetry/validity and inverse conversion | source tradeoff definitions/proof | not checked | unexamined | needed for complete conclusion transfer |

Candidates: `pSamplingOperator_ofDPEventBound_le_classicalSubsamplingEventBoundWitness` supplies a curve inequality; `classicalSubsamplingAppendixEventBoundWitness_le_beta` supplies a scalar inequality conditional on S and its five feasibility constraints. Neither signature contains arbitrary M or actual output laws. The local composition checks only the conditional scalar route and prints its full assumptions. It must not be reported as support for the complete source theorem.

Alternative inspected: `withIdentityWeightBranchPair` uses a branch-tagged density space Bool×α; forgetting the branch and matching general dataset kernels are additional obligations. Its compiled module is unavailable. `OptimalSubsamplingLaw.samplingLawMechanism` constructs a particular Gaussian-mixture source/reference mechanism, not arbitrary M. `FDPSubsamplingExactSurface` transports equal input objects, rather than constructing the hidden sampled law. These source inspections establish limitations of these routes only.
