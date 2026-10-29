# Existing norm routes and the remaining comparison

The existing formalization already has a **uniform full-jet estimate**, not
only the separate coordinate bounds replayed previously. Its constant is chosen
before the function, parameter set and input bound. It still loses five
orders. A fresh copied-source replay of that theorem completed with only
`propext`, `Classical.choice` and `Quot.sound`.

Two source-bound proof slices explain the difference precisely: inversion
instantiates the generic multiplier estimate at growth order **1**; removing
the mean instantiates it at **0**. The generic estimate asks for `n + l + 4`
input derivatives. Thus the four-order centering theorem is not a counterpart
to the paper's four-order inverse estimate.

This is answer-informed development evidence. No new mathematical error, exact
paper-norm bridge, native contract-production frontier or discovery benefit is
established. No production code or original paper/Lean source was changed.

## Existing declarations and their scope

All source locations below refer to the unchanged pinned formalization. The
[replay source](JetRouteReplay.lean) retains the complete original
`NavierStokes/SmoothFamilyTorusInverse.lean` before the appended observation goal.

| Obligation | Existing declaration | Established scope / remaining qualification |
|---|---|---|
| Bound derivatives through an order | `SmoothFamilyTorusInverse.JetBound`, line 652 | For every `j ≤ n`, parameter `p ∈ S`, and universal-cover point `Y`, the full joint iterated Fréchet derivative has norm at most `C`. It is not a newly defined conventional torus `C_y^n` norm. |
| Uniform generic multiplier estimate | `applyMultiplier_finiteJets`, line 847 | For multiplier growth order `l`, input order `n+l+4` controls output order `n`; the constant is chosen before multiplier, function, set and bounds. |
| Uniform inverse estimate | `inverse_finiteJets`, line 865 | Generic finite-dimensional parameter space retained; `∃ K ≥ 0, ∀ f S C, ...`. Input order `n+5` controls output order `n`. |
| Four-order mean removal | `nonbarPart_finiteJets`, line 1020 | Output is the mean-subtracted function, not its directional inverse; multiplier order is zero. |
| Real-valued adapter | `UniformFourierAlias.realInverse_finiteJets`, line 611 | Transfers the inverse estimate to real functions and explicitly retains `m+5`. Source-inspected here, not independently replayed in this round. |
| Reassociated parameter-family adapter | `UniformFourierAlias.familyInverse_finiteJets`, line 804 | Retains `m+5` and the actual `FiniteJetBound` on a shell. Source-inspected only. |

The full joint bound includes parameter derivatives. Matching it to a fixed
parameter torus function requires a suitable specialization and the relation
between coordinate derivative norms and tensor operator norms. Its existence
removes uncertainty about whether the original source has uniform constants
and simultaneous derivative bounds; it does not establish that remaining
interpretation or save the extra derivative.

## Checks through current checkout Ladon

The original repository's missing navigation index was built with the existing
CLI: 2,659 modules and 51,100 lexical declarations, with 746 recorded omissions.
It was fresh before the query batch and remains fresh afterward. Broad truncated
queries were refined to selected owners. Focused searches for `JetBound`,
`coeffSeminorm`, summability and four-order statements led to the declarations
above. The inspected summability route uses the fourth-power weight majorant.
A query for the literal cubic-weight form returned no match, which is **not**
a proof of semantic absence. See [search scope](SEARCH-SUMMARY.json), raw query
results and [source references](route-references.txt).

The two authored full-jet goals differ only by changing `n+5` to `n+4` in the
input `JetBound`. All type parameters, the finite-dimensional hypothesis,
smoothness, periodicity, bound sign and quantifier order remain fixed.
The public candidate checker accepted the original statement with no residuals
in 4.69 seconds and rejected the altered statement at application unification
in 4.63 seconds. These are ambient selected-application results; rejection does
not refute the altered proposition. See [probe contract](JET-PROBES.json) and
[results for five](jet-check-5.json) / [four](jet-check-4.json).

For stronger provenance, the exact original source was copied and the faithful
goal appended. Public source-goal capture/completion applied the existing theorem
`@NavierStokes.SmoothFamilyTorusInverse.inverse_finiteJets` without a new proof.
Fresh capture, recapture, application and independent source-context replay
produced six successful process receipts, no residuals and accepted standard
axioms. The whole command took **88.04 seconds**, peaking at **5.12 GiB** under
the unchanged 12 GiB cap. See [capture](jet-capture.json),
[completion](jet-completion.json) and [command](jet-replay-command.json).

The [inverse slice](inverse-slice.json) and [centering slice](centering-slice.json)
each contain one application of `applyMultiplier_finiteJets`. Their sixth
arguments are the actual natural literals 1 and 0, respectively, verified from
the structural expression graphs as well as displayed text. They took 23.38 and
23.10 seconds, each peaking at approximately 3.66 GiB. Slice identity, current
helper/source identity and shape all validate. Their finite-dimensional instance
premises remain explicit provider boundaries. This is proof extraction plus a
root interpretation of `n+l+4`; it is not automatic production of a mathematical
norm contract.

[Verification](VERIFICATION.json) checks those outcomes, exact submitted goal
and term bytes, all 2,670 original primary files, baseline inputs and all 57
artifacts in the previous provider packet. Historical reports remain unchanged.

## Paper interpretation and remaining adapter

Independent original-paper review found the four-loss arithmetic consistent
under the usual coordinate `C_y^m` norm. The fixed temporal direction is given
in (6.2), and (6.7) bounds its inverse divisor by one frequency power. Input
Fourier decay of order `m+4`, combined with `m` output derivatives and that one
power, leaves cubic decay on the two-dimensional lattice. This matches the
paper's explanation on page 96. The reviewer did not locate an explicit norm
definition in the supplied text; the conventional interpretation remains a
stated interpretation. See [source excerpts](PAPER-EXCERPTS.txt) and
[review and root reconciliation](REVIEW.jsonl), posts 1537–1538.

The generic formal estimate instead uses `summable_weight_inv_four` and a
coefficient seminorm estimate requiring four orders beyond its index. A sharper
route could use a cubic summable majorant and a coefficient estimate requiring
three orders beyond the index. The existing `coefficient_polynomial_bound`
provides arbitrary-order coefficient decay, but no assembled sharper inverse
route was located among the inspected owners and consumers. This names a
possible mathematical adapter; it is not a new Lean proof or a claim that the
adapter is absent everywhere. The auxiliary alias result containing
`m + 6*p + 4` has a different output and assumptions and was not substituted for
the inverse estimate.

For Ladon, the concrete capability boundary is now explicit: it can navigate,
check and extract these real applications, but its current formal-contract
producer cannot turn this Real-valued `JetBound`/paper-norm comparison into a
source-faithful contract. The next required evidence is that exact typed norm
interpretation and a checked sharper route, or an honestly unresolved comparison.
More traversal allowance, repeated closure replay, or treating the centering
lemma as an inverse theorem would not provide it. The user requested analysis
of the existing formalization, so no replacement theorem was formalized here.

The umbrella remains 8/12: tasks 2.1, 3.2, 3.3 and 3.4 retain their original
acceptance gates. No full suite, full-paper run, cache optimization, commit or
push was performed in this round.
