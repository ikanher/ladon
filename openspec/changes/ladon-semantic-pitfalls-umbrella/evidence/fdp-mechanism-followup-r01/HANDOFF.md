# MF follow-up: hidden fixed-size subsampling support

Status: prepared mathematical handoff, staged in Ladon. No MF change, proof run or new audit launched. This is a proposed theorem-development scope, not a claim that all missing mathematics is a small adapter.

## First action

Read the [U.7 report](../pitfalls-consumer-fdp-20261114T131246Z/REPORT.md), [application ledger](../pitfalls-consumer-fdp-20261114T131246Z/APPLICATION.md), and [checked conditional composition](../pitfalls-consumer-fdp-20261114T131246Z/Probe.lean). Verify identities against INPUTS.json in this packet. Use the Ladon checkout from its own root with `PYTHONPATH=src .venv/bin/python -m ladon.entrypoint`, rather than the pip executable. Retained lexical search is navigation only.

If adopted in MF, reconcile the existing source/theorem owners and archived packet boundaries listed below before creating or extending a local OpenSpec change. This packet does not authorize editing the donor from the Ladon audit session. Read MF's root, Mf, DP and OpenSpec guidance. Coordinate any builds; use an isolated build root.

## Outcome and first milestone

The parent question is whether the formal development supports the manuscript's arbitrary-mechanism subsampling theorem. First deliver a source-faithful construction of the hidden fixed-size sampled output law and a checked derivation of its classical testing-error constraints. A completed event-bound theorem is useful partial support; the full C_p endpoint remains a separate gate.

Source: `paper/theory/mu-dp/subsample.tex:35–75,161–201`; dataset adjacency: `fDP/fDP.tex:32`, included by `paper.tex:146`. Preserve same-size replace-one adjacency, individual slots including repeated values, uniform exactly-m selection, arbitrary M, and hidden sample identities.

**Interpretation clarification:** U.7 selected inherited ordering for the sampled tuple. The excerpt specifies a subset but does not explicitly choose a tuple ordering. Treat inherited ordering as an attributed reading that must be validated. For arbitrary order-sensitive M, randomized ordering, permutation invariance and inherited ordering are distinct mechanisms/assumptions. Do not silently substitute one. Resolve this at gate A before claiming a theorem for the prose. This clarification leaves U.7's unresolved-support verdict unchanged.

## Recipe and gates

### A. Fix the actual mathematical interface

- State D:Fin n→X and replace-one relation explicitly; choose a uniform probability law over slot subsets of cardinality m, with 1≤m≤n.
- Define the selected tuple in X^m, including ordering/randomness; prove the source interpretation used or retain competing readings.
- State M as a probability kernel/law-valued map and the original f-DP assumption through actual randomized hypothesis tests, with all measurability and valid-f conditions. Keep unsupported measure-space generality explicit. Do not replace arbitrary M with Gaussian noise.
- Protect definitions after choosing the claim. Added exchangeability/order assumptions create a separately labeled conditional claim.

Cheap risk check before theory expansion: for n=3,m=2, replacing slot 0 in subset {0,1} by slot 2 gives {1,2}. Their increasing-order tuples need not differ in only one position. Thus subset replacement alone does not prove tuple replace-one adjacency. Check the actual coupling/order map; this observation is not a source counterexample.

Deliverable: exact Lean statement/protected definitions and attributed source map; or a concrete unresolved interpretation. Do not invest in downstream proofs while the mechanism changes under the map.

### B. Construct the hidden output law

Define L_D as the normalized finite mixture of M(selected(D,I)) over the exact-count sampler, integrating any declared ordering randomness. Prove normalization/measurability, slot multiplicity, and the event/test expectation identity. The released variable contains only M's output. If a tagged law is used internally, prove its marginal identity under tag erasure. A tagged density pair alone does not close this gate.

Handle m=n separately where the excluded branch has zero mass; never divide by n-m without a guard.

### C. Discharge the existing classical route from M

For a neighboring pair and an arbitrary randomized test construct the actual included/excluded errors and `ClassicalSubsamplingAppendixState` with p=m/n, k=-exp ε, b=1-δ. Derive each of `ClassicalSubsamplingAppendixFeasible`'s five constraints:

1. sampled alpha decomposition;
2. sampled beta decomposition;
3. complementary excluded errors from identical excluded laws;
4. included privacy bound from the original M premise;
5. replacement/counting refinement with justified tuple adjacency.

Reuse `countedRefinement_of_replacementPointwiseBound` and `classicalSubsamplingAppendixEventBoundWitness_le_beta` where applicable. Their assumptions must be produced, not supplied as a new hfeas premise in the parent theorem. Check one consistently instantiated composition. Deliver a mechanism-level classical event inequality for all required tests and both neighboring directions.

### D. Transfer to the actual C_p conclusion

Distinguish the full testing trade-off from `PrivacyObject.tradeoffAt ε`, which is a fixed-ε affine profile witness. Establish the family-of-event-bounds conversion, inverse/symmetry/validity conditions, and the paper's convex-envelope/biconjugate map. Check any endpoint or lower-semicontinuity requirements. An operator named C_p or a pointwise upper bound by an affine witness is insufficient.

Final target under the validated reading: for every ordered neighboring D,D′ and every α∈[0,1], C_(m/n)(f)(α) ≤ T(L_D,L_D′)(α). Quantifying over ordered neighbors supplies both directions. Print the full theorem and permitted transitive axioms. Report every undischarged gate.

## Existing owners and prior packet boundaries

Inspect these existing MF paths before adding abstractions:

| Owner | Reusable result | Boundary |
| --- | --- | --- |
| `Mf/DP/FDPSubsampling.lean` | curve operations, convex envelope, monotonicity | no arbitrary sampled mechanism |
| `Mf/DP/TradeoffFunction.lean` | curve surface and fixed-ε affine witness | type name alone does not imply full testing semantics |
| `Mf/DP/ClassicalEventDPSubsetReplacementCounting.lean` | exact subset replacement/counting | requires pointwise inequalities and correct tuple map |
| `Mf/DP/ClassicalEventDPAppendixLP.lean` | LP implication from five feasibility constraints | does not construct testing errors |
| `Mf/DP/ClassicalEventDPProfileSubsampling.lean` | scalar sampled event endpoint | consumes hfeas |
| `Mf/DP/FDPSubsamplingWithIdentityExactSurface.lean` | represented Bool×α branch pair | requires actual marginal/output-law match |
| `Mf/DP/OptimalSubsamplingLaw.lean` | particular Gaussian-mixture law | narrower than arbitrary M |

Archived MF packets (read locally; do not reopen their completed scopes as if they proved this target):

- `openspec/changes/archive/2026-04-06-lean-fdp-subsampling-with-identity-law-pair-realization`: landed represented-pair layer; inspect actual realization limitations.
- `openspec/changes/archive/2026-04-10-lean-classical-event-dp-subsampling-theorem-and-poisson-consumer`: queue/boundary correction, explicitly not a full theorem delivery.
- `openspec/changes/archive/2026-04-05-lean-classical-event-dp-subsampling-bootstrap`: parameter and curve bootstrap.

## Acceptance and stop rules

Qualify at least: m=n boundary, m=1, constant-output M, repeated values at distinct slots, both neighboring directions, hidden versus tagged output, and the chosen ordering policy. A failed proof search is not a counterexample. A counterexample must satisfy all original assumptions in the chosen mechanism model.

For each completed gate retain the exact source judgment, theorem, arguments, proof receipt and transitive axioms; permitted axioms are propext, Classical.choice, Quot.sound. Separate ordinary Lean compilation from native completion/replay/trust and source fidelity. No sorry/admit/new axiom may close a gate.

No run budget is allocated by this planning handoff. On adoption, declare a finite proof budget and focused validation before execution; carry forward process bounds of 60 seconds, 12 GiB RSS and 8 MiB output unless explicitly changed. Missing compiled imports are operational, not mathematical evidence.

A complete gate-A interpretation assessment or a gate-B law constructor is a legitimate first result; neither completes C_p. If the bridge requires a substantial missing theory, deliver its exact statement/dependencies and stop expansion at the declared budget. Do not redefine the parent theorem to a Gaussian or branch-tagged special case.

## Return to Ladon

Return the exact theorem or residual, source map, receipts, failures and costs. Ladon's existing complete-application recipe can then consume it. Recommend a runtime feature only for a reproduced missing tool operation. No new comparative campaign or claim of natural-error detection follows from this handoff.
