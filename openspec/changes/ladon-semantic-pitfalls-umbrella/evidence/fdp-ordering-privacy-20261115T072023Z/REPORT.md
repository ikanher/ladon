# Inherited-order amplification countermodel

## Result and scope

**The claimed classical amplification bound fails under the explicitly inherited-order interpretation.** This is stronger than the earlier failure of a selected proof route. It is a checked finite counterexample to that interpreted mechanism claim, not an unqualified refutation of the paper: its subset-to-tuple ordering remains unresolved. No new Ladon detector or comparative benefit was established.

The inherited-order model chooses a uniform two-slot subset of three slots, supplies its increasing-order tuple to M, and releases only M's binary result. Neighbors differ in one tuple coordinate.

## Original mechanism and all assumptions

Let X={0,1,2,3}. On an ordered pair (a,b), M releases true with these probabilities (false has the complementary probability):

| a\b | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| 0 | 1/3 | 2/3 | 1/3 | 1/3 |
| 1 | 1/6 | 1/3 | 1/6 | 1/6 |
| 2 | 1/6 | 1/3 | 1/6 | 1/6 |
| 3 | 1/6 | 1/3 | 1/6 | 1/6 |

The finite law is normalized for every input. For every replace-one pair x,y and every binary output event E, P(M(x)∈E)≤2P(M(y)∈E). Ordered quantification gives both directions, including all 16 possible inputs and all four events. This is pure ε-DP at ε=log 2.

The Lean theorem `base_testing_bound` additionally covers every randomized binary test with real rejection probabilities u,v∈[0,1]. With α its rejection probability under M(x) and β its acceptance probability under M(y), it checks β≥max(0,1−2α,(1−α)/2). Thus the base pure-DP testing-curve obligation is discharged, rather than assumed for the candidate.

## Hidden sampled laws and violation

Take D=(0,1,2), D′=(3,1,2), actual replace-one neighbors. The increasing-order choices are (0,1), (0,2), (1,2); `selection_coverage` checks exhaustive slot-pair coverage. The probabilities of true after hidden sampling are

P=(2/3+1/3+1/6)/3=7/18,
Q=(1/3+1/6+1/6)/3=2/9.

The classical claimed factor is 1+(m/n)(2−1)=5/3. But

P−(5/3)Q=1/54>0.

This violates the actual event inequality with E={true}. Normalization of the sampled Bernoulli law is checked for every source dataset. No subset identity is released.

For the source's displayed pure-DP corollary, the sampled curve is max(f_(log(5/3),0)(α),1−(2/3)(2−1)/(2+1)−α). On the reversed neighboring pair, the deterministic test has α=Q=2/9 and β=1−P=11/18; the displayed curve equals 17/27, exceeding β by 1/54. `testing_bound_failure` checks the rational rendering of that formula. Its identification with the source C_p expression is the attributed use of the manuscript's corollary, not a new Lean proof about `TradeoffFunction.pSamplingOperator`.

## Checked control

Using the same M and original D,D′, uniformly sample ordered pairs of distinct slots instead. Then P_shuffled=11/36 and Q_shuffled=2/9. `shuffled_pair_control` checks the factor-5/3 event bound for all four output events in both directions for this pair. This is a local faithful control; no general shuffled-sampling theorem was proved. Changing the sampler changes the mechanism and cannot retroactively repair inherited ordering.

## Proof and discovery evidence

[Countermodel.lean](Countermodel.lean) contains the whole finite construction, original-premise checks, mixture and event calculations, randomized-test inequality and control. [attempt-07.json](attempt-07.json) is the accepted final ordinary Lean receipt; all printed axioms are drawn from propext, Classical.choice, Quot.sound. This is a finite rational probability encoding, with real-valued randomized tests and the real event violation also checked. It does not instantiate MF's measure-valued ApproxDP API or native source-goal completion.

[search.py](search.py) used a 16-variable LP for discovery. [search-result.json](search-result.json) rechecks the rational candidate on the full finite neighboring domain. No floating optimum is used as mathematical proof. System Python already had SciPy; the Ladon virtual environment did not. No dependency was installed.

Seven Lean attempts were retained: two passed, five failed. Initial drafts needed explicit case splitting because the finite product decision instance did not reduce; further failures concerned finite-numeral simplification and a cast. No failed draft is credited. `attempt-final.json` is a retained failed attempt despite its original filename; the accepted current receipt is explicitly attempt-07.json.

## Source consequence and next action

The source fixes coordinate replace-one adjacency in fDP/fDP.tex:32. Its appendix at property.tex:286–299 treats differently selected subsets as neighboring inputs without specifying tuple ordering. Under inherited ordering that inference can fail, and this countermodel shows the final classical bound can fail too. This rules out proving the unchanged inherited-order target by merely filling the earlier missing formal bridge.

The correct next source-level decision is to specify the intended dataset/sampler semantics, then prove the matching theorem. Uniform randomized ordering or a permutation-invariant mechanism are distinct candidate readings/conditional repairs. Neither has been silently added to the original claim. No theorem fault under a different sampler or unordered-dataset interpretation is claimed.

For Ladon, retain this as exposed development evidence for the existing object-map and small-countermodel recipes. Original assumptions and released law were checked before accepting the counterexample. A future regression must disclose author/workflow exposure and cannot count this as a held-out discovery. No runtime capability gap was reproduced.

## Scope and costs

The local 40-minute assessment ended at a completed selected result before its deadline. Selected source/direct-import hashes were verified again. The read-only MF checkout and old evidence were not edited. Ordinary Lean and finite-law reasoning provide the stated evidence; source interpretation, full library-law transport and independent review remain separate. Costs and failures are in COSTS.json; no resource stop occurred.
