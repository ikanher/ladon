# N.3c — exposed checked-application qualification

The seven frozen development expectations have been assessed with existing Ladon source-goal checks and ordinary Lean. The known faults are refuted by full stochastic models, faithful/derived/conditional cases have completed support, and the shifted-state route has a valid ordinary Lean proof. Native completion of that shifted proof remains unavailable because its closed-proof round-trip is rejected. This is not seven native completion successes and establishes no new detection advantage.

## Case results

| Case | Evidence and reader consequence |
| --- | --- |
| C01 faithful | Reuse the completed N.3u source-context application, conjunction/existential transfer, compiler replay and permitted trust result. The same frozen claim/owner is retained; this is prerequisite evidence reuse, not a new check. |
| C02 omitted sign | N.3u exposes the missing state-sign residual. `N3Singleton.lean` separately proves all original stochastic premises on Unit with dirac measure and X_n=−n,A=C=0,B=1, including a separate abs(C)-summability lemma; the B summability conclusion fails. Thus the source conjunction is false. We do not claim the X-divergence component was also compiled. |
| C03 conditional repair | `N3C03-complete.json`: completed, replay accepted, permitted standard axioms. This is the separately identified repaired conditional claim, not a proof of C02. |
| C04 derived sign | `N3C04-complete.json`: completed with square nonnegativity derived from X=Z² under the original X adaptation/integrability premises. No unstated regularity assumption on Z. |
| C05 shifted state | Direct application retains a state-sign residual. `N3ShiftedFull.lean` proves the full alternative theorem at Y=X+K and transfers convergence back with limit ≥−K, without adding integrability of A. Ordinary compiler/axiom output is accepted. Both native term attempts are rejected at closed-proof round-trip; they are not native support. |
| C06 shared parameter | Native completion rejects the attempted combined application: 1=1 was supplied where one shared n=0 requires 0=1. The conditional owner is valid; its premises cannot be fabricated from proofs at different instantiations. |
| C07 quantifier | Native conclusion transfer is rejected. `N3TwoPointRoot.lean` proves the full frozen half-counting Bool probability model, the original theorem's samplewise result and absence of a common a.s. limit. Thus the stronger source conclusion is false despite all owner premises holding. |

All final ordinary certificate runs exit successfully and their named theorem axiom reports contain only propext, Classical.choice and Quot.sound. `N3Summable.lean` also checks the pinned real absolute/norm-summability equivalence. Failed drafts/probes and their sorryAx warnings remain historical attempts, not certificate evidence. The generic C06 control concerns argument identity; it is not a probability-model counterexample.

## Native boundary and exact unresolved issue

The refined valid shifted-state proof (`N3C05-v2.term`) passes ordinary Lean when inserted into the unchanged wrapper context as `N3ShiftedFull.lean`. Native completion against `N3C05-capture.json` reports `typecheck-or-closure: closed proof round-trip changed its expression` before independent replay. It supplies no support/trust success. Source inspection identifies the closed-print/re-elaboration/definitional-equality boundary in `src/ladon/lean/ladon_source_goal_completion_helper.lean`; it does not identify which subexpression or condition causes failure. Do not weaken the boundary or assert a diagnosis without reproducing it.

The first draft also had a genuine rewrite-shape problem. Its ordinary compilation failed and it was corrected by making function addition explicit before rewriting conditional expectation. Only the corrected draft's ordinary success versus native rejection demonstrates the remaining limitation. Original failed artifacts are retained.

An ordinary Lean proof is already a valid way to audit this source claim. The missing capability, if future use needs it, is completing this exact valid term through the captured-goal replay route while retaining source/context, round-trip and axiom guards. No new diagnostic schema, universal translator or general provider graph is justified here.

## Context and ledger

`INPUTS.json`, retained wrappers/terms, captures and completion reports carry source-context bindings and actual residuals. `LEDGER.md` maps premise supply and conclusion transfer. The author knows the original theorem, cases and review answers. N.3b's source-only reading procedure was not independently behavior-tested here. Unchanged frozen expectations and identities are verified; source meaning remains an attributed interpretation.

The goal wrappers interpret C summability using the pinned real norm-equivalence check, not an ordered conditionally convergent series. Limits are samplewise, except for the deliberately strengthened C07 goal. No measurable-random-variable bridge is claimed beyond those explicit statements. A completed selected route is not a certificate of full-paper fidelity or proof-method correspondence.

## Execution and costs

`SESSION.json` fixes one 3600-second batch deadline. `DO.py` caps operations at min(600 seconds, remaining stage time), 12 GiB process-tree RSS and 16 MiB output. Setup reuses the retained local proof/dependency cache; it does not build in the donor. Two fresh-context Luna-medium workers attempted the singleton and two-point models; root integrated the singleton proof and repaired/completed the two-point implementation. This is implementation assistance, not independent review. The user's instruction removed the requirement to wait for a separate independent review; no independent-review acceptance is claimed.

Requests, streams and process receipts include unsuccessful attempts. Initial failed worker drafts are not all source-closed for replay; final certificate sources and root revision snapshots are retained. Time-to-query reporting is bounded by each recorded invocation start/result, with source interpretation work preceding them; complete mathematical thinking, worker scheduling, preparation/review and token accounting are unavailable. Counts/times do not estimate a productivity advantage. RESULT.json records total stage elapsed time, including failed attempts.

## Consolidation decision

Consolidate the whole-application recipe in the audit guide and bundled/shared skill, including derived premises, alternative routes, conclusion transfer and honest native failure handling. Use ordinary Lean where the completion helper rejects a valid proof. Preserve the minimal C05 reproduction for a focused compatibility follow-up if a real consumer needs it. Another broad optional-tool comparison is not warranted by these exposed successes.

The next meaningful investment decision is whether a reliable checked-application workflow adds useful evidence or reduces work against the same mathematical recipe with ordinary Lean. A future comparison needs one specific additional capability, fresh inputs and a frozen prediction; none was launched here. Stop semantic-diagnostic expansion if no distinct contribution emerges. Recommend superseding broad three-stage integration as the automatic investment roadmap, retaining accepted baselines and individual regression cases; that retirement remains a scope recommendation, not a retroactive pass or deletion of historical requirements.
