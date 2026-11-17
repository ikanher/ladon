# Ladon r04 strategy and implementation review

17 November 2026

## Recommendation

**Keep the native MF capability and pause broad ProofIR expansion. Make the next milestone a reader who correctly reconstructs the claim and its assumptions from the existing evidence, at an acceptable total cost.** Fix the remaining large-inventory diagnostic-recording gap, then observe one actual internal reader handoff using the current guide. Only a demonstrated difficulty should trigger a narrow definition and source-context view or a comparative experiment.

r04 changes the engineering assessment: two richer MF examples now pass through the public native production and inspection route. It does not change the comparative product assessment. The proofs and interpretations were supplied, the important mathematics already existed, and no fresh discovery, reader-benefit or total-effort advantage has been measured. The most promising next investment is clearer access to the definitions and hypotheses hidden behind a selected wrapper, followed by a test of whether that access changes judgments or work. [E1, E2]

The broader goal is coherent: preserve a trustworthy connection between mathematical exposition and its formal support, including actual objects, assumptions, quantifiers and reasoning. The infrastructure advances that goal when it helps a reader resolve a consequential question. Repeatedly certifying increasingly elaborate wrappers can become a diversion if the source-to-wrapper attribution remains unexamined.

This review proposes work; it applies no repository change and launches no new auditor experiment. The included read-only Python probes examine source behavior, finite arithmetic and retained records. They do not run Lean or the complete Ladon test suite.

## What changes from the r03 assessment

| Question | r04 assessment | Consequence |
| --- | --- | --- |
| Can the native route handle these larger MF environments? | Yes for the two retained successful cases, after bounded serialization repairs. | The next milestone need not be another supplied-proof qualification. |
| Are the wrappers mathematically legitimate? | The inspected wrappers preserve the original proofs and the intended conditional statements. | Do not dismiss the results merely because a final transfer is simple. |
| Does successful wrapper checking establish source fidelity? | No. The essential source reading and object construction still precede the native check. | The source-to-wrapper boundary needs reader review. |
| Is a necessary relationship demonstrably missing from ProofIR? | No general expressiveness failure is established. Some definition bodies and contextual source spans are not delivered by current inspection. | Test a bounded retrieval/presentation improvement before proposing a new schema. |
| Do the new results establish comparative value? | No. The earlier negative comparisons and scoring correction are unchanged. | Retain a competent ordinary-Lean baseline and full cost accounting. |

The two original mathematical files are byte-identical to their r03 copies and exact prefixes of the new wrappers. All 20 implementation files present in both packets are also byte-identical; the canonicalizer and several support/test files are newly included in r04. Packet differences therefore cannot reconstruct the canonicalizer's pre-repair text. This review assesses the current implementation and reported repair history without claiming a complete before-and-after code diff. [E1, E3]

The earlier synthetic result remains two useful fault findings for control versus one for assistance, with an assisted false reassurance. In Unit 03, the first interpretation already imported state nonnegativity; the final report later saw the formal premise and still authorized the original passage. A larger representation has not been shown to fix that combination of interpretation drift and evidence misclassification. Unit 05 retains conditional almost-sure support with source intent unresolved. [E4]

## DP-Adam preserves the mathematics but changes the visible premise boundary

### The wrapper is not circular

`AdamNative.Inputs` contains primitive data and hypotheses. It does not contain the desired common-law convergence result. `commonLaw` places one existential probability law outside the conjunction of two actual process-limit claims, and `bridge` applies the existing `paired_source_convergence` with the input projections. The original theorem constructs the pair using `source_convergence` and a checked equality of the limiting laws. [E5, E6]

The meaning is:

```text
For every a : Inputs, there exists a law μ such that
the first process family for a converges to μ, and
the second process family for a converges to the same μ.
```

The law may depend on `a`. This is not one law shared by every possible choice of input, nor equality of finite-run distributions. It also supplies no uniform finite-run rate, equality of finite accountants, simultaneous-beta scaling, or completed source-method audit.

The native conclusion-transfer goal is essentially `commonLaw a → commonLaw a`. That is legitimate tracking of an already established proposition. The nontrivial construction and convergence proof occur inside the preserved theorem and definitions; the final identity-shaped transfer cannot independently establish that those definitions express what the prose asks the reader to believe.

### Zero premise rows do not mean zero assumptions

The original scoped extraction in `adam-slice.json` contains 20 local declarations and six direct proposition premises at the selected `source_convergence` application. The wrapper extraction has one non-Prop local, `a : Inputs`, and zero premise rows. Both native MF plans contain zero `premise-supply` obligations while displaying `premiseEstablishment: supported`. [E6, E7]

This is consistent with the selected theorem type: its hypotheses are packaged inside `Inputs` and its nested `Primitives`. It is not a kernel soundness error or semantic erasure. It is a concrete consumer risk. A reader who interprets the displayed dimension as a completed source-assumption audit can be falsely reassured.

The report should distinguish **no direct premise-supply obligations at this selected boundary** from **the packaged assumptions have been matched to the source**. It should expose the relevant record fields and retain the original scoped application as a separate observation. That observation concerns one selected application, not the entire original proof.

There is no need for a universal nonvacuity gate on every conditional theorem. Realizability matters when the exposition asserts that an actual object or application satisfies the conditions. The essential requirement is to avoid silently treating possession of an `Inputs` value as a verified source-to-input construction.

### The source anchor is narrower than the attributed claim

The checked Adam anchor covers `adam-source.tex` lines 425-465: privacy calibration and the explicit schedule, ending mid-sentence. Those bytes match the recorded hash and quote. The excerpt alone does not state the two-family common-law claim or its query conditions. Relevant surrounding source includes clock/initialization assumptions, the fixed-query assumptions, and the diffusion theorem with uniqueness. [E8]

This is a source-attribution gap requiring contextual justification, not evidence that the mathematical consequence is false. The source reading should say that common-law support is derived from those linked passages and definitions. A short, accurately hashed quotation cannot stand in for that reasoning.

The native interpretation authoring format currently accepts one source span, while the generic source-map payload already supports multiple anchors. Additional contextual attachments could improve navigation through existing artifact types. They would still be attributed context, not a proof that every record field faithfully captures the prose. Do not assume that the current authoring CLI already supports that composition. [E9]

## f-DP remains a conditional counterexample with separate premise evidence

The f-DP wrapper preserves the original countermodel. `bridge` uses the existing strict inequality, the Nat argument is a dummy application index, and `neighbor` aliases the original neighboring dataset. The native refutation shows that the checked strict inequality cannot imply the attributed factor-5/3 upper bound. The source file also separately proves the negation of that exact interpreted consequence. [E10]

The normalization, base privacy, adjacency, randomized-test argument and actual inherited-order sampler remain established in the preserved prefix. They are not independently enumerated as native premise-supply rows in the new wrapper. The native numerical transfer is therefore one part of the source counterexample's justification, rather than a replacement for the rest of it.

Independent exact-rational recomputation confirms all 384 directed adjacent-input/event checks for the factor-2 base mechanism, and the sampled separation:

```text
P_D(true) = 7/18
P_D'(true) = 2/9
7/18 - (5/3)(2/9) = 1/54 > 0
```

The shuffled sampler gives 11/36 and 2/9 for this pair and satisfies its selected bound. That does not prove a general shuffled-sampling repair. The manuscript's subset-to-ordered-tuple policy remains unspecified, so the warranted finding is conditional refutation under inherited order plus unresolved source interpretation. No unconditional manuscript falsity or full measure-valued tradeoff-API theorem follows. [E10, E11]

This example is a useful guardrail for reader-facing output. A refuted correspondence link must remain distinct from a separately justified counterexample to a source interpretation. The earlier true-source/wrong-map control remains a complementary guardrail against false accusations. [E12]

## Implementation findings

### P2: large inventories can still prevent recording two unresolved outcomes

The capacity repair is appropriately narrow on the inspected success paths. Recognized module collections receive a 32,768-item cap; unrelated collections and nested lists inside module rows retain the generic 10,000-item cap. Canonical encoding remains sorted, compact UTF-8 JSON, and the reviewed byte/hash checks preserve existing identities. Marker recognition selects a size profile; it does not establish semantic admission or authenticity. [E13]

A remaining gap occurs on two early `_check_goal` returns in `correspondence_check.py`: `prepared-goal-subject-mismatch` and `unexpected-generated-goal-context`. Both can retain a captured compiled inventory, but neither includes `goalOrigin: generated-correspondence-obligation`. `_check_supplied_terms` preserves that omission. `completion_artifacts` then calls `_row_artifacts`, which hashes the receipt before producing the unresolved diagnostic artifact. The canonicalizer's `_receipt_module_paths` does not grant the larger inventory capacity without that origin marker. [E14]

The isolated exact-source reproduction evaluates those return expressions and the actual artifact-hash path. Both constructed diagnostic states fail with `collection exceeds item limit: 10000`, first using 10,001 synthetic module rows and then using the unchanged retained Adam capture with 12,221 modules. The same diagnostic hashes at 10,000; adding the exact origin marker allows the larger captured inventory.

**This is a failure-recording reliability defect, not evidence of false proof acceptance.** Neither diagnostic occurred in the two retained successful runs. The verification proves the serialization behavior if those branches are taken; it does not claim a fresh native Lean reproduction of the diagnostic state.

Carry the same generated-obligation origin consistently through diagnostic outcomes, or pass an explicit narrowly scoped capacity profile at the trusted call site. Add regression coverage for both unresolved paths above 10,000 modules and rejection beyond 32,768. Preserve their unresolved status, semantic validators and replay/trust requirements. Broadly relaxing every list named `modules` would be the wrong repair.

The review's 79 bounded Python assertions cover capacity boundaries, path isolation, nested/byte/depth restrictions, exact canonical encodings, retained artifact IDs, receipt hashes and the diagnostic paths. They are separate from the packet's reported 184-test suite, which was not rerun here.

### P3: the telemetry still overstates the role of object-map checks

`substantiveCheckCount` excludes only the `interpretation` obligation. It therefore includes the object-map typing goal ending in `True`. Both r04 cases report one typing and three substantive checks, although each consists of two typing/elaboration checks, a conditional replay and a conclusion transfer. Adam's final transfer is identity-shaped. [E14]

Report obligation roles directly. Eight accepted checks are procedural checks for two supplied interpretations, not eight discoveries, eight premise audits or eight independent confirmations of source fidelity. This classification issue was already present in r03.

### The existing authority distinctions still matter

`matched-stored-records` compares the selected plan/obligation, exact target digest, checked polarity, status and operation. It does not authenticate origin or perform fresh replay. `coverage.complete` is retrieval completeness and can coexist with open or refuted links. `welltypedness` checks `P → P`; current `representation-transport` checks typed map expressions followed by `True`. Stored producer dimensions remain separate from reviewed prose fidelity. [E15]

Inspection does not reconcile every result/guarantee/trust field in a separately authored or damaged checker record. The normal native producer derives these fields consistently and requires accepted replay/trust before emitting support. No native false-support path was demonstrated. Additional contradiction diagnostics are optional robustness work if imported or damaged records become a real use case; they would not authenticate fabricated self-consistent records.

The 32,768 count is also not a peak-memory guarantee or an assurance that every such inventory fits within the byte cap. Aggregate encoded-byte limits are checked after serialization. This review does not attribute the observed nine-GiB proof-process memory to canonicalization.

## Cost and scale

The final successful numbers agree with the retained top-level process receipts. [E16]

| Case | Successful native check | Sampled outer peak RSS | Recorded closure modules | Stored inspection |
| --- | --- | --- | --- | --- |
| f-DP | 498.732 s | 8.992 GiB | 11,034 | 1.148 s |
| DP-Adam | 447.573 s | 9.459 GiB | 12,222 | 1.591 s |

The surrounding closure counts differ by one from each retained capture inventory, which has 11,033 or 12,221 modules. They describe different records and should not be silently interchanged.

| Retained scope | Operations | Unsuccessful | Sum of top-level command-wall durations |
| --- | --- | --- | --- |
| Final successful checks | 2 | 0 | 946.305 s |
| All check attempts | 7 | 5 | 2,776.553 s |
| All native process receipts | 22 | 10 | 2,897.754 s |

The ten unsuccessful operations account for 1,844.742 summed command-seconds. The ledger includes three initial timeouts, two f-DP and one Adam, as well as the subsequent 488.037- and 441.280-second serialization failures.

These are **overlapping command-wall sums, not project elapsed time or CPU time**. The final checks ran concurrently. Interpretation authoring, wrapper construction, source review, donor-cache preparation, some development work and total adjudication effort remain unmeasured. The run therefore supports feasibility of this route and exposes its cost, without establishing a causal speedup or product return.

The two sequential typing-only obligation stages consumed 208.354 seconds for f-DP and 189.429 seconds for Adam, approximately 41.8% and 42.3% of the outer successful check durations. This is a profiling lead, not a prediction that 42% can be removed. Nested capture/completion stage times overlap and must not be added to these figures.

The immediately useful distinction is already available: producing new native evidence takes minutes; producing the stored inspection view took 1.148 and 1.591 seconds. Reader comprehension and review time were not measured. Start reader work from the stored view with its historical authority explicit. Require new replay when the task needs current proof assurance. Profile production work only if actual usage shows that it is the limiting cost, preserving source/environment identity and trust checks.

## Bounded next work package

### First, close the diagnostic gap and conduct one real handoff

Keep the capacity repair, fix its diagnostic branch coverage, and correct the telemetry labels. Use a short capped iteration; five engineering days is a suggested spending ceiling, not an evidence-derived estimate. Neither fixing this bug nor adding a label justifies broader semantic machinery.

Give an actual intended consumer the current guide and one selected MF question. Ask for a source-faithful verdict, exact formal meaning, assumptions, unresolved scope and the evidence they used. Observe which lookup or interpretation is costly. The current guide already instructs readers to inspect `Inputs`, `commonLaw`, argument producers and the original countermodel. The question is whether that procedure is usable and followed. [E17]

If the ordinary workflow already produces a justified answer at acceptable cost, stop at consolidation and normal-use feedback. Do not commission another general comparison merely because a qualification checklist is complete. The packet's 12/12 status is a task checklist, not a reader-success rate.

### If there is a concrete lookup problem, prototype bounded definition context

The archive includes `definition-context-example.md`, a worked review artifact showing the exact kind of context a reader needs. It is answer-bearing and is not fresh evaluation input. For a fair experiment, create a separate mechanical excerpt view without its explanatory verdicts.

The candidate operation is a bounded, owner-qualified lookup of declarations referenced by the selected formula, object types and application. For Adam, the immediate useful material is `Inputs`, `Primitives`, `commonLaw`, `bridge` and the original paired-convergence application, followed only as needed by `sourceData` and `resample`. Preserve full quantifier order and distinguish type fields, definitions, theorem applications and unexpanded frontiers.

| Design question | Narrow proposed answer |
| --- | --- |
| Exact subject/relation | A selected formula/object/application references a named declaration whose type, fields or definition body the reader needs. Separately, an attributed interpretation depends on identified contextual source spans. |
| Producer | Existing declaration/source navigation and exact stored owners; source-context selections remain attributed. Check the current explain/constructor/source capabilities before adding another extractor. |
| Consumer | The auditor reconstructing the claim and matching its hypotheses to the source; later reviewers checking the same decision. |
| Authority | Recorded declaration/source evidence in its pinned environment. Displaying a dependency is not proof that the prose matches it or that the proof necessarily uses every field. |
| Bounds | Explicit declaration and byte limits, requested expansion only, with omitted/unexpanded frontiers. Avoid recursive expansion of an entire import closure. |

Current inspection does not automatically expose those definition bodies. Their mathematical content remains in the preserved source, and other navigation operations may already retrieve it. The demonstrated gap is a display/lookup boundary, not a demonstrated need for a new canonical relationship type. Prototype with existing attachments and source maps; change a producer or query only if the current route fails the observed task.

Contextual source anchors should make the common-law attribution reviewable, including the clock, query and diffusion passages. Merely adding references does not establish premise equivalence. Keep source interpretation review and actual source-to-input construction explicit.

### Dependencies, parallel work and follow-through

The diagnostic fix and telemetry cleanup can proceed independently of the reader handoff. The handoff should precede a production definition-view feature. Source-attribution clarification can proceed alongside the view prototype, but any improved interpretation must be given equally to both comparison arms. Reference adjudication and cost instrumentation can be prepared in parallel once the task and output contract are fixed.

Defer universal prose translation, a larger assumption graph, new canonical artifact kinds, automatic semantic dependency inference and a paper-specific adapter. The existing derivation hypergraph already expresses AND premises and OR alternatives. Missing mathematical laws or sampler-repair results require proofs, not another metadata layer. [E18]

## Smallest falsifiable evaluation

The first question is deliberately narrow: **does easier access to the same definitions and source context improve claim reconstruction or reduce total effort?** It is not a test of autonomous prose discovery or a new proof-search algorithm.

If the handoff exposes a relevant difficulty, use the two MF cases as known evidence-reading tasks, with two fresh sessions per case: ordinary Lean/source navigation and the same recipe, versus that workflow plus the mechanical definition view. Keep model/version, settings, budget, supplied interpretations, owners, source, exact goals and underlying proof evidence equivalent. Give both arms the same declaration names and source-span identifiers: the treatment receives mechanically rendered contents, while control retrieves them through ordinary navigation. The treatment must not receive expert-written maps, diagnoses or stronger interpretations absent from the control. Both arms must cite the exact definitions and evidence supporting their answer. If the view also selects better references, label the intervention selection plus delivery and account for that selection work.

The four primary sessions can decide whether the concrete interface idea merits further work. They cannot establish a population reliability rate. A fresh reader of an exposed case is not a fresh mathematical discovery. Do not give auditors this review or its answer-bearing worked example.

Predeclare the consequential answers. For Adam, the reader must preserve one law within each input pair, the dependence on packaged hypotheses, and the absence of finite-run equivalence or newly checked whole-source coverage. For f-DP, the reader must identify inherited ordering, the separately justified original premises/law, and the difference between link refutation and unconditional manuscript falsity. Have mathematical review assess those conclusions without tool-identifying logs where feasible; assess cost separately and disclose remaining exposure.

Require zero serious false reassurance or false accusation in the treatment on these observed tasks, including errors shared by both arms. Also require useful justified support: blanket abstention is inadequate. Predeclare Adam then f-DP as the repeat-selection order and repeat the first pair with a consequential difference, regardless of which arm it favors. Preserve every primary and repeated outcome. A claimed consequential improvement must recur in that fresh paired repeat; if the selected repeat concerns a treatment regression, stop expansion pending diagnosis. For a cost-only claim with equally justified verdicts, repeat the matched trace and include preparation/review costs. A disappearing advantage is inconclusive; do not keep retrying.

Before treating the view as generally safer, add a small held-out guardrail where the source is true but the selected route fails, and a faithful derived-premise case. Those distinguish useful caution from false accusation. Only a promising result warrants a separately chosen real prose-first task with the source reading frozen before revealing the candidate owner. Score interpretation selection separately from supplied-evidence checking.

For economics, retain human time, model usage, wall time and resource use separately unless conversion weights are declared. Count reusable preparation, per-audit work and study-only duplicated review separately. Choose the expected reuse horizon and worthwhile margin before seeing timings. The relevant break-even condition is that accumulated per-use savings exceed additional preparation and maintenance, while judgment quality remains adequate.

## Additional ideas worth retaining conditionally

**Test invariance to harmless packaging.** Present an equivalent claim with inline hypotheses, a structure argument and a named predicate. The justified source verdict should remain the same. Add a deliberately altered common-law quantifier as a separate negative control. This directly tests whether readers are overusing superficial premise counts or support labels; it is a controlled robustness test, not proof of natural-error discovery.

**Expose the boundary before enlarging the graph.** A small report distinction such as direct premise count, hypotheses packaged in argument types, and unresolved definition/source context could prevent overreading `premiseEstablishment`. Do not automatically classify every field as necessary: DP-Adam's earlier objective-field irrelevance example shows why actual dependence matters.

**Profile only demonstrated production bottlenecks.** If users frequently create new evidence and the replay cost dominates, use the recorded stages to investigate shared preparation or batching with exact identity and freshness checks. First establish a matched baseline. Do not skip trust checks or promise savings from the typing-stage percentage.

## Success, stopping and the next review

| Observation | Investment decision |
| --- | --- |
| Ordinary navigation already serves the reader | Consolidate the current route and collect normal-use feedback. No definition feature is required. |
| Same evidence plus definition delivery yields repeatable better judgments or full-cost savings | Implement one bounded view using existing identities/artifacts and reassess on a fresh source task. |
| Definitions are available but the source reading remains wrong | Invest in interpretation reconciliation and independent review rather than schema expansion. |
| The missing connection is an unproved equality, constructor or sampler result | Do the bounded mathematics and preserve its unresolved scope. |
| A repeated real task cannot preserve or retrieve an exact needed relation | Specify that relation, producer, consumer and authority, then justify a narrow representation change. |
| No judgment or cost advantage survives the declared repeat | Stop this expansion and keep the current capability optional. A negative result does not invalidate all Ladon navigation or evidence storage. |

The next review should receive the diagnostic regression result, exact reader inputs and outputs, interpretation history, definition/source lookup trace, independent adjudication and a full cost ledger. Another collection of supplied successful replays, an improved checklist count or a larger artifact does not resolve the investment question.

## Verification and provenance

The review verified all 382 r04 manifest-listed files and all 293 r03 entries without mismatches; the current native manifest's 70 entries also matched. The original proof prefixes, source anchor bytes, eight retained completion/replay/trust records and exact goal/polarity bindings were checked. Every artifact content ID and check-receipt hash in the two selected r04 MF bundles was recomputed in isolated exact-source Python probes. Finite countermodel arithmetic was independently recomputed. The included scripts and raw derived results make those checks repeatable.

The packet lacks the complete Python runtime, Lean executable and compiled dependency closure required for full native replication. The reported 184 tests and original Lean runs remain reported/retained evidence, not new executions in this review. Hashes establish byte consistency, not origin authentication or mathematical meaning. Input archives and source files were not modified.

r04 metadata says no r03 response was received; the earlier review is present in this conversation. The bundle includes that memo for continuity. This provenance mismatch does not change the mathematical results, and no r04 change is assumed to have been made in response to that review.

Confidence: 96% in the verified capacity/diagnostic behavior; 95% in the mathematical wrapper analysis; 98% in the retained cost arithmetic; 89% in the investment recommendation. These are judgmental confidence levels, not statistical reliability estimates.

## Evidence index

Paths are relative to the included `ladon-semantic-strategy-review-data-r04/` directory. In the paths below, `N` abbreviates `sources/openspec/changes/ladon-proofir-correspondence-context/evidence/mf-native-r01/`; `P` abbreviates `sources/openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/`.

- **E1:** `N/REPORT.md`, `RESULT.json`, `FINAL-SELECTION.json`, `PYTEST-RECEIPT.txt`; top-level `REVIEW_PROMPT.md` and `REVIEW_DELTA.md`.
- **E2:** `BRIEF.md`; unchanged historical comparison reports listed in `EVIDENCE_MAP.md`.
- **E3:** `verification/input-verification.json` in this review bundle; `N/project/Fdp.lean`, `N/adam-project/AdamCase.lean`; original `P/fdp-ordering-privacy-20261115T072023Z/Countermodel.lean` and `P/dpadam-source-constructor-r01/Full.lean`.
- **E4:** `P/synthetic-launch-r01/SCORING-CORRECTION-v1.md`; `experiment/unit-03/assisted/outputs/FIRST-INTERPRETATIONS.md` and `FINDINGS.md`; original control findings.
- **E5:** `N/adam-project/AdamCase.lean`, declarations `AdamNative.Inputs`, `commonLaw`, `bridge`, `selected`; `LadonSourceConstructor.paired_source_convergence` and `sourceLaw_resample`.
- **E6:** `N/adam-slice.json`, `N/adam/aligned.json`, `N/adam/checked-1800-r02.json`.
- **E7:** `N/adam/inspection.json`, `N/fdp/inspection.json`; `sources/src/ladon/correspondence_check.py`, `_summarize_premises`.
- **E8:** `N/adam/interpretation.json`; `N/adam-project/adam-source.tex`, clock/initialization, fixed record queries, diffusion/uniqueness, privacy calibration and explicit schedule passages.
- **E9:** `sources/src/ladon/correspondence_interpretation.py`, `validate_interpretation`; `proofir_correspondence.py`, `interpretation_artifacts`; `proofir_correspondence_payloads.py`, `_has_exact_anchor`; `proofir_v3_payloads.py`, source-map validator.
- **E10:** `N/project/Fdp.lean`, `N/fdp/interpretation.json`, `N/fdp/terms.json`, `N/fdp/checked-1800-r02.json`; original finite countermodel under P.
- **E11:** `P/fdp-source-interpretation-r01/INTERPRETATION.md`, `HASH-CORRECTION-20261116.md`; retained three source TeX files under the original countermodel directory.
- **E12:** `sources/openspec/changes/ladon-proofir-correspondence-context/evidence/mathematical-controls-r01/REPORT.md` and retained wrong-map/uniform bundles.
- **E13:** `sources/src/ladon/proofir_v3.py`, `canonical_bytes`, `_slice_module_paths`, `_receipt_module_paths`, `_validate_list_bounds`, `_validate_object_bounds`; `sources/tests/test_large_correspondence_inventory.py` and related capacity tests.
- **E14:** `sources/src/ladon/correspondence_check.py`, `_check_goal`, `_check_supplied_terms`, `check_correspondence`; `correspondence_evidence.py`, `_row_artifacts`, `completion_artifacts`; `correspondence_cli.py`, `_check`.
- **E15:** `sources/src/ladon/proofir_v3_queries.py`, `query_v3_correspondence`, `_compare_stored_binding`, `_attach_check_evidence`; `correspondence_evidence.py`, `_accepted`.
- **E16:** The 22 `N/*.process.json` receipts; `N/*/checked-1800-r02.json`, `executionAccounting`; `sources/src/ladon/correspondence_execution_accounting.py`. Derived ledger: `verification/eval-checks/native-process-ledger.csv` in this bundle.
- **E17:** `sources/docs/PROOF_CORRESPONDENCE_AUDIT.md`, Read the native MF examples; owning change `tasks.md` for the 12/12 qualification checklist.
- **E18:** `sources/openspec/specs/proofir-derivation-hypergraph-semantics/spec.md`; `sources/src/ladon/proofir_derivation.py` and companion solver/slice/core modules.
