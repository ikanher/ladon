# Gate A: ordering is a substantive part of the sampled mechanism

## Outcome

**Interpretation assessment complete; source ordering remains unresolved.** The source defines replace-one adjacency on tuples, and the appendix describes the sampled input as the individuals indexed by a subset. The inspected passages do not specify an ordering/randomization map from subsets to tuples. The removed wording about permutation in the source is a comment, not an active assumption. We cannot certify inherited ordering as the uniquely intended mechanism.

No source theorem refutation, f-DP counterexample, new runtime defect, or completed mechanism theorem is established. This is a semantic boundary control: two plausible object maps lead to different observable laws.

## Checked evidence

[Ordering.lean](Ordering.lean) uses the existing donor imports without modifying them. [attempt-02.json](attempt-02.json) records successful ordinary Lean compilation and the permitted axiom sets.

| Obligation | Declaration | Result and limit |
| --- | --- | --- |
| Same selected slots, one changed source slot | selected_agree_off | generic in n,m,X,D,D′ and injective selection e; all other selected coordinates agree |
| Changed source slot excluded | selected_eq_of_excluded | full selected tuple equality |
| Replace a selected index at its original position | replacement_injective, replacement_agree_off | injection is preserved when the new slot was absent; tuples agree off the replaced coordinate |
| Re-sort after replacing an index | sorted_replacement_not_agree_off | for n=3,m=2, increasing tuples [0,1] and [1,2] disagree in both coordinates |
| Ordering changes output law | ordering_changes_output_law | exact finite-uniform tally: M(tuple)=first slot value on distinct-valued D=(0,1,2) outputs 0 with probability 2/3 under increasing subsets, versus 1/3 under uniform ordered injections |

`AgreeOff` permits equality: it establishes at-most-one coordinate change. Applying a privacy assumption stated for exactly-one changes still requires the usual identical-input case. The example mechanism is used only to distinguish output laws; no privacy guarantee for it is asserted. Uniform finite probabilities are represented by cardinality ratios in this control; no general probability-kernel theorem was proved.

The first draft failed because `decide` could not see through `AgreeOff` to synthesize its finite decision instance. Unfolding the definition fixed it; the failing source and receipt are retained. The final output-law control enumerates the actual finite choice spaces and counts, rather than assuming their probabilities as premises.

## Source map and consequence

Source inputs are copied under inputs/. `fDP/fDP.tex:32` fixes equal-size coordinate replace-one neighbors. `subsample.tex:37` describes uniform subsets. `appendices/property.tex:230` defines x_I by the indexed individuals, and its replacement argument at lines 288 onward requires adjacency between differently selected inputs. It does not explicitly discharge the tuple-ordering map.

Same-subset neighbors pose no difficulty under an injective selection. Replaced-subset neighbors require more care. The checked failure of sorted coordinate adjacency prevents using subset counting alone as its producer. It does not show that every possible coupling or proof fails, or that the final privacy theorem fails under inherited ordering.

A uniform ordered-injection model can retain the replacement coordinate in place. Its general tuple lemmas are checked here. Its uniform law, coupling/multiplicity, and source equivalence remain unproved. Permutation-invariant mechanisms offer another possible conditional route, but the source's arbitrary-M statement must not silently acquire that extra assumption.

## Remaining parent obligation and next action

Gate A has delivered the handoff's permitted result: conditional checked facts plus a concrete unresolved interpretation. Gate B and the arbitrary-M C_p theorem remain open. Before constructing a purported source law, choose and justify the intended sampler/tuple policy. Then prove its normalization, hidden output marginal and coupling; the generic in-place lemmas can be reused for an ordered-injection route. If a conditional alternative is developed, label it separately from source support.

This evidence strengthens Ladon's existing object-map recipe: sampler names, uniform subset marginals and matching count parameters do not establish the released output law. No new production checker is justified by this example. Ladon was not newly invoked for theorem discovery in this continuation; retained U.7 navigation was reused. Mathematical checks used ordinary Lean.

## Bounds and evidence limits

The 40-minute local assessment ended after completing the declared interpretation check, before its deadline. Two Lean attempts, one failed and one successful; no time, output or memory stop. All selected source/direct-import hashes were reverified. No native completion or independent review was performed; no transitive freshness claim is made. Donor sources, index and compiled artifacts were not written.
