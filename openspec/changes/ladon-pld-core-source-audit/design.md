# Design

Current execution status is owned by [tasks.md](tasks.md). The revised bounded audit is complete; [REPORT-v2.md](evidence/pld-core-r03/REPORT-v2.md) and its adjudication supersede the earlier completion report and record the source formula finding, independent review and partial coverage.

## Context

See [proposal.md](proposal.md) for the decision to audit the DP core. The [completed premise comparison](../ladon-premise-provenance/evidence/premise-comparison-m2-r01/ADJUDICATION.md) supports the evidence discipline, not a new discovery claim. The source survey inspected actual Lean statements and local paper sources; it did not freshly compile them. Navigation with this Ladon checkout found a fresh lexical index, which is not compiled proof authority.

The target checkout is `../lean/matrix-factorization`, resolved relative to Ladon's root. Read its root and scoped instructions before using it; preserve concurrent work. The user's instruction to use this Ladon checkout takes precedence over that repository's installed-CLI preference.

## Goals / Non-Goals

**Goals:** let another mathematical reader resolve the selected local questions from source-linked evidence, while exercising premise provenance, feasibility and operation-property checks where the passage needs them. Record what Ladon contributes to selecting, checking or explaining an obligation.

**Non-goals:** assume a fault exists, prove all PLD/f-DP theory, complete an unresolved mathematical programme, create artificial discrepancies to guarantee a positive score, or implement diagnostic stages before a need is demonstrated. This is exposed development, not a blind experiment or a matched cost comparison.

## Decisions

### Selected sources and candidate owners

Paths in this table are relative to the mathematical checkout. Declaration names are navigation anchors to verify against the pinned source, not accepted mappings.

| Role | Source or formal owner | Scope to freeze |
| --- | --- | --- |
| Primary exposition | `paper/theory/numerical-composition/PRV.tex` | PRV definition and surrounding conventions; complete theorem blocks `thm:PRV_LLRV`, `thm:PRV_privacycurve`, `thm:composition_PRVs`, including the composition proof and claims in displayed formulas |
| Proof/context inputs | `paper/theory/numerical-composition/appendix_PRV.tex`, `prelims.tex`, `MAIN.tex`, and macro files actually needed | Corresponding proofs, privacy-curve/composition definitions and referenced hypotheses; record exact included and excluded spans |
| Event/positive-region bridge | `Mf/DP/PrivacyLossCore.lean` | `privacyLossSet_bound_iff_dp_event_bound` and its integral hypotheses |
| Density-to-law bridge | `Mf/DP/Profile/ConcretePLDPair.lean` | `expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local`, with the definitions it consumes |
| PLD object and actual product realization | `Mf/DP/PLDRandomAllocation.lean`, `Mf/DP/PLDCompositionApproxDP.lean` | `PLDPair`, `comp`, `compFamily`, and `concretePLDPair_sharedBaseProduct_eq_compFamily`; definitions of concrete laws and loss maps may live in imports |
| Candidate faithful control | `paper/theory/improving-gaussian-mechanism/centered-bridge-note.tex` | The setup and View A–C reduction, through “What must be matched exactly”; retain the declared positive-radius restriction on displayed CDF formulas |
| Gaussian control owners | `Mf/DP/FiniteGaussianPrivacy.lean`, `Mf/DP/GaussianPrivacyLoss.lean`, `Mf/DP/LawAccountingOracle.lean` | Find the actual positive-region, projection and event-profile support for the selected control; the historical `GaussianCore.lean` facade is navigation only |

Freeze entire small source files for context, but enumerate selected spans. A theorem block containing several assertions gets several inventory rows. In particular, do not silently omit a converse, endpoint or intermediate equality because the first candidate Lean theorem does not cover it. Missing formal support stays in the inventory with its precise status.

This selection reuses established mathematical owners rather than a supplied diagnosis. The planner has read the source and some status reports; record that exposure. Do not label the exercise blind. No reference verdict is supplied for the PLD passage. The Gaussian passage is a control candidate, not a guaranteed pass.

### Alternatives and later sequence

| Candidate | Decision and reason |
| --- | --- |
| Full f-DP duality/subsampling | Reserve. Exact hypothesis-testing tradeoffs, fixed-epsilon linear witnesses and PLD-backed representations need careful distinction; a named interface is not proof of the complete literature theorem. Use only necessary definitions in this audit. |
| Subsampling Is Not Magic | Later known-correction regression. Its closure map supplies reference answers about calibration and limits; keep that answer material out of fresh auditor inputs. |
| Historical stochastic approximation / Adam | Later harder audit of conditional expectations, normalization and convergence modes. Preserve source theorems versus modern sufficient models. |
| DP-Adam / DP-SGD convergence | Later application audit of actual algorithms and applicability gates; existing reviewed DP-SGD material remains historical control evidence. |
| BIFR | Later exploratory audit. An openly conditional result or unresolved certificate is not automatically an exposition error. Unknown answers complicate comparative scoring. |
| Navier–Stokes | Later known-fault regression, after a useful workflow and separately declared comparison. Fresh auditors get isolated sources without prior findings or diagnoses. This plan records no fault location, mechanism or solution. |

There is no automatic launch of any successor. The same LLM with ordinary Lean and the same recipes is the eventual comparator. Equal source access, budgets and search opportunity, inaccessible answer material, independently reviewed outcomes and a predeclared benefit threshold belong to that separate registration. This audit does not choose a numerical improvement threshold or change the frozen 24-case baseline.

### Execution recipe

Use [the correspondence guide](../../../docs/PROOF_CORRESPONDENCE_AUDIT.md) and [source-first discovery](../../../docs/CORRESPONDENCE_DISCOVERY.md). The steps below specialize those existing procedures; ordinary files suffice and no production schema is added.

#### 1. Freeze inputs and start the effort record

1. Create a new `evidence/<run-id>/` under this change, failing on collision. Create separate `inputs/`, `work/` and `review/` directories. Do not write into previous accepted evidence or the mathematical source checkout.
2. Record the two checkout roots, commits and relevant dirty-source identities; copy selected source files, needed macro/context files and exact Lean owners. Record each original path, SHA-256 and selected line spans. Include the pinned Lean toolchain and Lake manifest. Additional imports discovered later receive dated manifest additions; do not replace the first input manifest.
3. Read relevant source context before attributing an omission. Record source labels and any definition outside the selected passage that supplies a hypothesis or convention. If a required source cannot be obtained locally, make that dependency unresolved rather than narrowing the claim silently. No online search for reference answers is needed.
4. Verify the local runtime, for example `.venv/bin/ladon version --json` from Ladon's root. Inspect current subcommand help and resolve the actual implementation path. Record bounds and actual command lines. Run `proof-search index status --changed` once per query batch; use stored queries only against that recorded generation while sources are unchanged. Source search remains usable if the index is incomplete.
5. Start timestamps and an effort ledger before interpretation/checking. Account separately for input preparation, interpretation, checking, review and corrections; record token usage only when available. Previously paid evidence is reuse, not zero-cost end-to-end work.

Planning does not freeze a run deadline or certify inputs. At execution initialize a shared 3,600-second checking deadline, a ceiling rather than a required wait. Keep the 12 GiB process-tree cap and current finite output/depth limits; record all effective limits. Run at most one heavy Lean/extraction process at a time. Input preparation and human/model review are timed separately and cannot renew an expired checking deadline. This is a local audit, not a required 90-minute full-paper run.

#### 2. Inventory and freeze first interpretations

Read the whole selected passage before selecting proof slices. Write `INVENTORY.md` with one row per mathematical assertion found: source ID/span, original context, attributed meaning, quantified variables, assumptions, object/law map, proposed formal support, and examined/unexamined state. Record how completeness was assessed. A first interpretation is attributed, not certified.

Keep the paper's orientation of laws and loss variables explicit; do not identify its notation with similarly named Lean fields by spelling. Preserve normalization, supports, finite versus extended values, measure versus density, independence and quantifier order. Identify where a conclusion is supplied as an interface premise and where an actual producer establishes it. Review log/division/integral/infimum properties only when claimed; total operations alone are not defects. Do not manufacture three separate diagnostic studies.

Hash the first inventory and interpretation record before proof attempts. Freeze the exact closed target and context for each later selected check before running it. Record corrections as separate versions with reasons. Select at least one consequential PLD obligation and one comparably substantive Gaussian control obligation, with source-based reasons; keep all other rows visible. No hand-picked final theorem can discharge unexamined intermediate claims.

Before theorem lookup, perform a source consistency pass on each selected assertion: list the defining equalities for its symbols; substitute any claimed inverse/reconstruction back into those definitions; check signs, reciprocal factors, directions and parameter endpoints. If inconsistent, construct a premise-satisfying example in the stated mathematical domain. Record this as source reasoning separately from Lean authority. Lack of a formal counterpart must not prevent checking an elementary source identity. Review acceptance must join by the frozen claim ID and source label, with unmatched IDs explicitly rejected.

#### 3. Establish support and check disputed steps

1. Search candidate types/names with local Ladon and inspect their full source statements and relevant definitions. Use the smallest owner/import scope. An empty lexical result is not absence; a definition or package name is not a theorem of realization.
2. Write the exact object map and required direction: do the source assumptions supply the formal premises, and does that result supply the source conclusion? Distinguish mathematical falsity, statement-scope mismatch, valid alternate proof method and unavailable formal support.
3. Use ordinary Lean or existing capture/completion/check commands for local obligations. Generated checks import actual owners, preserve dependent locals and let values, and may not assume their own conclusion. Independent feasibility checks must close outside the questioned assumptions. A refutation targets the fully closed original claim or supplies an assignment satisfying its premises and falsifying its conclusion; `H → ¬Q` alone does not refute `H → Q`.
4. If the judgment concerns how the existing proof works, inspect the original proof body and obtain a selected actual-use observation when necessary. A newly constructed proof of the same type is support for that proposition, not evidence of the original method. Scoped provenance joins use structural IDs, not display names.
5. Check selected owners/obligations using the pinned toolchain in an isolated work root or a coordinated existing build context. Bind imported compiled evidence to source/toolchain identities; source hashes alone do not prove compiled freshness. Preserve commands, exit status, logs, actual targets and axiom/replay evidence. Ordinary Lean checks and Ladon independent replay remain separate authority levels. Do not claim a full dependency replay from a local import check.
6. Retain failed attempts, unsupported operations, resource stops and unexpanded frontiers. Observe Ladon's memory-stop instruction: stop dependent progress and report to the user; do not silently raise caps. If a local operation fails, state whether existing source evidence or ordinary Lean can answer the question before proposing any new capability.

A conventional mathematical argument may resolve a source question even when its Lean counterpart is absent; label it as independently reviewed mathematical evidence. A failed tactic, missing adapter or stronger sufficient theorem is not a counterexample. A proposed repair has a different claim identity and never replaces the original.

#### 4. Freeze first findings and obtain independent review

Deliver `FINDINGS.md`, `EVIDENCE.md` and `EFFORT.json` (ordinary experimental records, no new canonical schemas). For every inventory row report supported, discrepancy, unresolved or unexamined, with distinct formal-support, source-fidelity and method judgments. Every discrepancy needs the exact claim, context, decisive evidence and reader consequence. Every accepted control needs affirmative support. A clean compilation alone does not establish fidelity.

Report what Ladon actually added, which work ordinary Lean/source reading performed, retained historical costs, and unresolved extraction/replay coverage. Hash the first findings and evidence manifest before review; never edit frozen reports in place.

An independent reviewer who did not author the findings receives the unchanged sources, interpreted obligations and raw evidence, with proposed verdicts withheld for their first assessment. If probe export is used, follow its existing sanitized-review contract. Ask the reviewer to check inventory omissions, scope/representation maps, legitimate conditions, counterexample premises, proof authority and the control. They first record their own dispositions; only afterward reconcile against the frozen findings. Attribute model/person and actual timestamps. Use Luna medium for routine delegated work per the user's preference; escalate a disputed mathematical question to root or the user, without silently changing worker models.

Write `REVIEW.md`, a separate correction addendum if needed, and a final `REPORT.md` binding hashes to the accepted versions. Interpretive uncertainty may remain unresolved. A second reader must be able to state what was established, which assumptions it uses, and what it changes about reading the passage.

#### 5. Close the bounded exercise and choose a disposition

The report can close with upheld discrepancies, justified controls, or an independently reviewed unresolved boundary. Review and reporting tasks cannot close merely because time expired or a file exists. Explicit unresolved/unexamined rows remain incomplete mathematical coverage even when the bounded reporting task is complete.

Choose one supported disposition: existing tools suffice for this scope; a concrete missing operation warrants a narrowly specified follow-up; or a useful completed workflow warrants preparing a fresh comparison. For an engineering follow-up, record the exact blocked claim, failing command/evidence, missing input/output and why an existing route is insufficient. Route it through the relevant child's preserved correctness/acceptance gates. No general graph, schema, cache or budget expansion follows automatically.

The development success criterion is a useful, independently upheld reader explanation, with at least one substantive PLD question and the candidate control resolved or their exact unresolved boundary reviewed. It is not “find one bug.” No detection/cost advantage can be inferred without the separate matched comparison. Do not launch that comparison or Navier–Stokes from this packet.

## Risks / Trade-offs

- **Candidate formalization is narrower than the prose** → preserve the original claim and scope gap; inspect related owners before declaring support absent. Do not build a large missing formalization to finish this audit.
- **A small theorem needs a large import closure** → first attempt one selected local obligation under the shared deadline and 12 GiB cap. Record blocked compilation/extraction and review the mathematical evidence; full capsules are optional only if a concrete authority question requires one.
- **Known diagnoses or source-selection cues bias the exercise** → retain exposure statements; separate development from any later fresh evaluation. A fixed positive-density specialization cannot certify a broader source claim without a bridge.
- **Control is harder or less faithful than expected** → retain its original ID and result, including ambiguity. Do not silently replace it with an easy passing control.
- **Infrastructure consumes the mathematics budget** → stop at the bounded failure, preserve the source question and propose only a demonstrated missing operation.

## Migration Plan

No production migration. Audit artifacts are additive, frozen outputs receive addenda, and sibling mathematical sources remain inputs. Update the parent task pointer and disposition after review. Diagnostic specifications, historical baseline populations and previously accepted evidence are preserved.
