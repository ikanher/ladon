# Review correction r02

This addendum supersedes the completion and no-fault conclusions in REPORT.md and RECONCILIATION.md. Those records, the first findings, raw output and their manifests remain unchanged. This is an exposed source review, with no new Lean execution and no online research. All 15 input hashes and all 12 report-manifest artifact hashes were verified during this review.

## Mathematical finding: P3 has an incorrect exponent

Frozen PRV.tex:15 defines y(t) = exp(t) x(t). Lines 50–54 (eqn:PRV_from_delta) assert y(t) = δ″(t) − δ′(t) and x(t) = exp(t)(δ″(t) − δ′(t)). The second expression conflicts with the definition: its multiplier must be exp(−t).

This remains false for smooth strictly positive normalized densities, so regularity restrictions do not repair it. Let p(t)=φ(t+1/2), q(t)=φ(t−1/2), the densities of N(−1/2,1) and N(1/2,1). Then q/p=exp(t), so the log likelihood is the identity, X has density p and Y has density q. Both laws have total mass one, positive smooth densities, and no endpoint mass. By the paper's privacy-curve convention,

δ(s) = ∫_s^∞ q(t) dt − exp(s) ∫_s^∞ p(t) dt.

Differentiation gives δ′(s)=−exp(s)∫_s^∞p(t)dt and δ″(s)−δ′(s)=exp(s)p(s)=q(s). At s=1 the printed reconstruction of X gives exp(2)p(1), whereas the actual density is p(1)>0. The corrected reconstruction exp(−s)(δ″−δ′) gives p(s). This is a source formula error, potentially a typographical error; it is not a refutation of the underlying PRV theory or a Lean theorem. The appendix derives only the Y recovery (appendix_PRV.tex:73–81), so its valid differentiation does not validate the erroneous X expression.

A separate Luna-medium reviewer independently checked this prompted candidate and the smooth witness; see REVIEW-CORRECTION-r02.md. This is independently checked mathematical evidence, not a kernel-checked counterexample and not an automated Ladon discovery.

## Audit defects requiring correction

1. **Claim IDs drifted.** The frozen inventory defines P2=LLRV, P3=privacy-curve formulas/converse, P4=independent composition. The original reviewer called P3 “P2” and reviewed Gaussian PRV laws as “P4”. The reconciliation imported that mistake. Thus the original review did not independently check the selected P4 question. The new source review checks the density-product argument against the independence definition in prelims.tex:23–25, but does not certify arbitrary singular/extended-law cases or a complete Lean correspondence.
2. **Inventory spans are inaccurate/incomplete.** G1's cited lines 10–59 do not include its log-ratio/projection claims. G2's cited lines 61–110 do not contain the radial/envelope assertions, which occur at lines 178–186 and elsewhere. Split P3's several equalities and converse into stable subclaims. Use labels and verified lines in a new inventory version; retain the original. The note's later endpoint-transfer theorem at line 375 uses Δ≥0 although H was defined only for Δ>0 at lines 147–155. This is a separate unadjudicated boundary question outside the initially selected early passage, not an accepted second fault.
3. **The Gaussian control changed scope.** The selected G1/G2 concern extremal-event and radial/envelope assertions for real ε. The checked theorem is a one-way sufficient bound with ε≥0 and δ<1. It supplies useful restricted support, but does not pass the original control. The narrowed implication must have its own identity and its assumptions attributed. Retain G1/G2 as unresolved until their actual statements are reconciled.
4. **Evidence authority and chronology were overstated.** The Lean file contains #check and three #print axioms commands; it observes imported signatures/trust lists, not new proofs of source correspondence. Source-to-compiled freshness was not established. FINDINGS has a pre-review freeze record, but the complete evidence/effort manifest was created after review and EVIDENCE was edited to include reviewer conclusions. Do not call that complete set frozen before review or retroactively create such a record. The original unsuccessful name query's output is absent. EVIDENCE also prints ../ladon from the matrix-factorization checkout; the relative path to this repository is ../../ladon. Treat the corrected path as a reproduction instruction, not proof of the historical invocation.
5. **Resource and cost claims lack receipts.** A declared 12-GiB limit plus a timeout command does not establish memory enforcement or measured peak usage. REPORT's claim that the run stayed under that cap is unsupported. EFFORT's 192-second checking interval has no raw shell timing receipt, and the reviewer duration is approximate. These are estimates/records of uncertain provenance, not measurements for a cost comparison. Do not report unavailable RSS or tokens as zero.

## Current disposition

P1 and broad P2 remain unresolved. P3's X reconstruction is a mathematically established source discrepancy under the smooth Gaussian witness above. The remaining P3 subclaims remain separate questions. P4's positive-density independent-product argument is consistent with the source's independence convention; the exact Lean object map and general-law extension remain incomplete. G1/G2 remain unresolved in their original scope; the restricted one-way theorem is adjacent support only.

The audit is reopened. No new Ladon production operation is yet justified. The demonstrated weakness is the audit recipe's failure to compare displayed equalities against nearby definitions, keep claim IDs stable, and enforce coverage at review acceptance. Correct those steps before a benchmark or broader implementation. No comparative advantage can be claimed from this exposed review.
