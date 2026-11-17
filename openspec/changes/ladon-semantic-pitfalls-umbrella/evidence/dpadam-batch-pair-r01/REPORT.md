# DP-Adam batch-pair audit — 2026-11-14

## Result

**No mathematical error was established. There is checked substantive support for the fixed-beta square-root scaling mechanism, beyond the earlier scalar identities. The general exposition-to-family bridge remains unverified.**

The new ordinary Lean proof constructs actual initialized, sampled DP-Adam families for a one-record quadratic, for every fixed sampling probability `0 < q ≤ 1`. It proves that changing the sampling probability and the diverging count sequence, with the same positive calibration coefficients, preserves their limiting path law and sufficient asymptotic stationarity bound. Both actual finite mechanisms eventually satisfy the same privacy target under the displayed calibration. The paired specialization uses `q' = k q`, `T_j = k(j+1)`, `T'_j = j+1`: expected epoch counts match at each index and the actual learning rates differ by `sqrt(k)`.

This is an informed root audit and constructed positive control, **not** an independent discovery experiment or a certification of all losses covered by the manuscript. The user-selected source is the newer natural-language diffusion manuscript found through Malladi references. The exact passage in the broader MF report is still unidentified. The manuscript itself distinguishes its fixed-beta regime from Malladi's regime; no overclaim is attributed to it here.

## Meaning for the reader

The checked consequence is consistent with this rule, under shared dataset, queries, clipping, fixed momentum, initial limit and public bounds:

- `B' = k B`, `q' = k q ≤ 1`, and `T' = T/k` with admissible integer counts;
- `eta = c/sqrt(T)` and `eta' = sqrt(k) eta`;
- `sigma_DP = B sqrt(gamma T)` and `sigma_DP' = sqrt(k) sigma_DP`;
- common slow horizon `H = c/sqrt(gamma)` and clock product `lambda = c sqrt(gamma)`.

The generic scalar identities and equality of actual family coefficient inputs are checked in [BatchPair.lean](lean/BatchPair.lean). The actual-family control and its consumers are checked in [SampledFamily.lean](lean/SampledFamily.lean). They use the same family data throughout; neither law equality nor the utility conclusion is introduced as a premise.

This does **not** transfer Malladi's whole non-DP recipe. Its local scaling section also changes the beta parameters and numerical stabilizer. Here beta is fixed, and the tuned coefficient contains `sigma_beta²`; changing beta requires another comparison of response and covariance. Nor does this give equal finite trajectories, identical finite privacy accountants, a finite-run error rate, or the learning rate that optimizes actual training performance. The coefficient minimizes the stated sufficient bound. Expected epochs match between paired runs at each index but grow along the limit. Sampling probabilities and the batch ratio are fixed along each family; no uniform result as `q` varies with the family index was checked.

## Exact evidence and limits

| Question | Result | Authority |
| --- | --- | --- |
| Does the leading privacy slope cancel q when B=qN? | Yes, under the original theorem's normalization and positive target gap. | Ladon source capture, completion, round-trip, separate compiler replay and standard-axiom trust accepted. [Summary](NATIVE-SUMMARY.json). |
| Are clipped mean, beta input, drift, covariance and tuned coefficient common for compatible supplied families? | Yes, under the explicit equalities in `BatchPair.lean`. | Ordinary Lean; these are conditional comparison lemmas, not constructors. |
| Can an actual non-full-batch family be built? | Yes for the centered one-record quadratic: arbitrary q in (0,1], beta1=beta2=1/2, C=1, normalized stabilizer=1, initial point 2. | `sampledData`, including release-kernel measurability for every private subset, regularity and exact clock fields. |
| Do the actual path laws share a limit? | Yes for those concrete families. | `sampled_convergence`, `sampledLimitLaw_eq`, `paired_convergence`, `matched_epoch_pair`. Solution-map uniqueness removes dependence on the chosen Lipschitz bound. |
| Do they meet the same privacy target? | Eventually, for integer order ≥2, 0<delta<1, epsilon above the conversion term, positive slack, and gamma equal to the source calibration with N=1. | `sampled_privacy`; uses the actual path mechanism and strict receipt margin. No common explicit first index supplied. |
| Is utility transferred to actual finite iterates? | Yes for this control: the expected retained-node penalty is eventually below a common sufficient bound plus any positive tolerance. | `sampled_finite_rate`, `sampledRate_eq`. Uses the finite expectation-transfer theorem, not weak convergence alone. |
| Does this close the general source claim? | No. | No checked constructor from arbitrary source record losses/public initial sequences to both formal families, and no complete general paired application, was retained. This is unresolved support, not a counterexample or proof that no constructor exists elsewhere. |

The concrete utility quantity is the actual average over retained left nodes of `min(x², |x|)`, integrated against the actual transcript law. The retained bound is the theorem's expression with objective `x²/2`, gap 2, dispersion 0, Hessian upper bound 1 and C=d=1. Algebraically it is `4/(alpha_beta H) + lambda sigma_beta²/alpha_beta`. It is independent of q and the count sequence when gamma,c and beta are shared. The final Lean target retains the original trace/gain expression; the simplified scalar display is a mathematical reading of that expression, not a separate newly checked simplification theorem.

The authored investigation terminates `incomplete-blocked`: 23 grouped claim records, two reviewed scalar/calibration groups and 21 groups with explicit missing reviewed support. This is an evidence-coverage boundary, not an environmental outage or a claim that further mathematics is impossible. The positive-control results above do not relabel those broad source groups as complete.

The full arbitrary-loss statement and the explanation of every reference/FCLT/adaptive-error step in the 558-line source inventory were not independently certified. The [premise ledger](PREMISE-LEDGER.md) records the precise generalization boundary. Imported Lean owners were checked through existing compiled imports; this packet does not contain the full dependency closure for portable independent replay. The native result checks the subordinate cancellation goal, **not** the entire paired stochastic claim natively.

## Interpretations and preserved failures

The preliminary assessment and first reading are preserved in [preliminary](preliminary/REPORT.md); [HANDOFF.md](HANDOFF.md) freezes the proposed pair before its construction. Prior source/theorem exposure is explicit. The consequential interpretation correction is that “fixed epochs” means paired equal epochs at each index, not a finite epoch budget held constant while T tends to infinity. The full source excerpt and hash/range are in [SCOPE.json](SCOPE.json).

Two generic-proof attempts and eleven concrete-family attempts are retained in `attempts/`, with source snapshots before subsequent changes. The first generic attempt had a missing namespace and an unsuitable algebra tactic. Concrete failures involved changed record fields, omitted section hypotheses, notation, definitional equality/casts and final conclusion simplification. These are failed audit proof drafts, not Ladon defects or evidence against the mathematics. Failed compiler outputs containing `sorryAx` are rejected attempts; only final successful files with standard axiom output support the result.

The final durable sources were checked again using the recorded runner. Their receipts include source hashes, unchanged-source checks, exact commands, timing and memory. No donor sources, dependencies, index or shared build outputs were written; no Lake build was run. Final input verification is in `INPUT-VERIFICATION.json`.

## Costs and tool contribution

The field clock began at 08:42:28 UTC with a 40-minute ceiling. The native completion command took 96.36 seconds wall time (92.56 seconds inside the operation), with four supervised Lean subprocesses, each under the 60-second process bound. Peak observed process-tree RSS was 9,532,571,648 bytes, about **8.88 GiB**, below the existing 12 GiB cap. There were no memory, timeout or output-limit stops. Ordinary Lean checks were approximately 3–6 seconds each, with final concrete proof peak around 6.96 GiB. `COSTS.json` records measured attempt totals and final timing; token cost and separately timed human/setup/review effort are unavailable. Native completion's operation time is not end-to-end audit time.

Ladon contributed source-context capture and replay/trust checking of a relevant cancellation, lexical navigation, resource-bounded execution and explicit investigation bookkeeping. The root authored the interpretation and the new ordinary Lean compositions. There is no evidence here that Ladon found something ordinary Lean with the same recipe would miss, or that it saved total effort. The stored lineage miss in the preliminary assessment remains `not_ingested`, not a theorem-absence claim.

## Disposition

**Consolidate the existing checked-application recipe; no production feature or default change is justified by this exercise.** The default resource bounds handled the substantive native request. U.2–U.4 can close as an informed internal-use record with explicit residual mathematics, without closing any historical detection gate.

The next mathematical obligation, if broader certification is wanted, is specific: construct both actual families from the manuscript's arbitrary fixed record queries, public initialization and release-measurability assumptions; preserve their shared object map; discharge local mean/initial coherence; then apply the named-law, eventual privacy and finite-iterate utility consumers with conclusion transfer. The concrete control demonstrates a working route and avoids treating supplied family records as an existence proof. It does not make that general obligation disappear. A later comparison with Malladi's simultaneous beta changes is a different proposition.
