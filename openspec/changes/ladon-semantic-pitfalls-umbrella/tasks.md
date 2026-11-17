# Tasks

## Current status and next steps

**Internal 0.4.4 release qualified — 2026-11-17.** The local versioned candidate
`78b2fc8` passes isolated distribution and pinned-Lean checks. The complete
selected integration suite, repository static quality, OpenSpec and skills pass.
[Release notes](../../../docs/RELEASE_0_4_4.md) and
[verification receipt](../../../docs/releases/0.4.4/verification.json) own exact
counts, identity and remaining qualification limits. F.1–F.4, H.1–H.3, V.1a
and V.2 are delivered. Persistent cross-process V.1 and compact inspection remain
open. No push or publication; historical mathematical acceptance stays intact.

**Explicit cleanup applied — 2026-11-17.** At the owner's request, the public
history-cleanup command removed MF's 50 stale catalog entries. A fresh preview
observed no remaining archive files; the operation deleted zero file bytes.
The active index remains available. The owner had previously deleted the
historical directory. See the appended cleanup/continuation record in
[evidence](evidence/dpsgd043-feedback/CLEANUP-AND-TIMINGS.md).


**Owner direction — retire automatic index archives (2026-11-17).** The owner
reports no remembered use requiring historical index snapshots and rejects
their continuing disk cost. Replace retention/rotation work with a disposable
current-index design. Derived search/lineage observations may be invalidated
and regenerated; intentionally saved audit artifacts remain ordinary explicit
outputs. Do not build a new archive system merely to preserve every cache row.
The completed history feature is historical behavior, not a requirement for
this next design. See [design](design.md#disposable-current-index-and-explicit-results).

[Implementation and verification](evidence/dpsgd043-feedback/HISTORY-IMPLEMENTATION.md)
record the delivered current-cache behavior and explicit legacy cleanup.

Completed scope:

- [x] H.1 Classify index-owned rows versus separately saved artifacts and check public consumers. Define observable invalidation when old cached observations disappear; preserve explicitly saved outputs without promoting them to current evidence.
- [x] H.2 Remove automatic whole-index archival from ordinary updates. Keep atomic publication and failure recovery through temporary candidate files, clean them after success, and let current search work independently of obsolete archives. Test updates with derived evidence and no-op updates, with no new persistent archive and no false freshness upgrade.
- [x] H.3 Provide a concrete catalog-aware cleanup preview for existing history, including paths, bytes and loss of historical lookup. Apply only explicitly selected cleanup; handle interruption without corrupting the active index. Document the changed default and replace obsolete archive-preservation expectations with the new contract.

The owner confirmed personally deleting the donor's snapshot files. The catalog
still lists 50 entries; the preview observes zero existing bytes. The owner then explicitly authorized catalog cleanup, which has now completed
through the public command (50 rows, zero file bytes). Reusable freshness tokens and compact slice views remain separate
possible follow-ups; an automatic retention service is no longer the next step.

**Additional consumer report — 2026-11-17, measured follow-up.** A second
user reports 58.8 s for unchanged-index checking, 75.7 s for an earlier
three-module update, approximately 993 MB active storage and 48.9 GB history.
Priorities: cheap generation comparison, visible phase timings, configurable
retention and a reusable freshness token. No raw receipts accompanied this
report; the user has not rerun the large-capsule workload. Record these as
reported observations, not a diagnosed cause or memory qualification.
The authorized DP-SGD follow-up is active. The read-only profile attributes 54.631 of 72.778 status seconds to hashing
50 historical databases. A focused current-generation check took 5.848 seconds
unprofiled. See [profile](evidence/dpsgd043-feedback/STATUS-PROFILE.json); these
are different measurement modes, not a controlled speedup estimate. Snapshot
sharing must retain explicit source freshness semantics. No history deletion follows from this request.


**Internal 0.4.3 consumer feedback — received and reconciled 2026-11-17.**
MF supplied `temp/dpsgd-exposition-ladon043-feedback.zip` (SHA-256
`8250543933237ceb7439ca5dc3b3a701c519cc9907cd9d373cd38d4a198c1495`),
reporting use of Ladon `94cfb203f304f9a7cbe98e0e98507b69c8177f9b` with a
dirty checkout. This assisted, non-blind DP-SGD exposition review reports useful
exact search, selected application slicing and historical stored-context
inspection; it makes no new discovery or native correspondence claim. Received
friction: missing slice time/RSS controls, expensive comprehensive index status,
inconsistent name/type-text provenance, bulky slice output and a scattered
exposition recipe. A deliberately selected 4 GiB candidate cap was exhausted;
the separately launched slice reportedly succeeded under 12 GiB. Neither report
identifies the memory or status-latency cause. The initial receipt marked these
claims pending validation before verification began.

[Reconciliation and next-work recommendation](evidence/dpsgd043-feedback/RECONCILIATION.md)
verify 54 manifest entries, 15 current donor bindings, slice identity and retained
summary fields. Source/help inspection confirms missing slice resource options;
a temporary lexical fixture reproduces absent stored type-text provenance.
Recommend a bounded follow-up for slice time/RSS controls, generation-bound
search provenance and a short exposition recipe. Assess compact slice delivery
from saved evidence; measure freshness costs before adding caching or a new
operation. Keep the 12 GiB default: the failed candidate explicitly selected
4 GiB. No bundled script, fresh Lean run, candidate retry or production change
was performed. The user authorized the bounded implementation; the completed release and
historical acceptance boundaries below remain intact.

### Remaining shared-freshness outcomes

The owner's full feedback recap confirms the following remain unimplemented:

- [ ] V.1 Shared read-only reuse of one validated generation across batch callers, keyed by source/configuration/toolchain and index identity. Define subsequent-edit invalidation and coordinated writer behavior; agent identity is not a freshness key. A generation ID alone is not an authorization token or a guarantee that live files remain unchanged.
- [x] V.1a Deliver the bounded batch route: 1–32 existing name/type-text queries, one SQLite read transaction, source/configuration/toolchain observations before/after, exact generation provenance, withheld results on edits/replacement, bounded transport and worker-shareable saved results. See [batch evidence](evidence/dpsgd043-feedback/BATCH-IMPLEMENTATION.md).

V.1's persistent cross-process token/invalidation behavior remains open. V.1a
provides shared validation within one declared batch; it does not certify later
queries without revalidation. The MF two-query exercise matched standalone rows
and generations: 5.658 s and 5.749 s separately versus 5.834 s together, one
sequential observation with uncontrolled cache/order effects.

- [x] V.2 Visible incremental-update timings for enumeration, hashing, extraction and database work. The continuation delivers all four phases with exclusive wall-time accounting on changed/no-op updates. The historical 75.7-second operation itself remains unprofiled.

Scoped, untruncated navigation and lexical/compiled authority distinctions are
positive received feedback. Historical capsule memory qualification remains
unreplayed and is not established by freshness or archive changes. The original
retention request is superseded by the owner-selected current-cache default.

### F: internal consumer follow-up

[Implementation and verification](evidence/dpsgd043-feedback/IMPLEMENTATION.md)
own the completed scope and remaining work.

- [x] F.1 Expose slice process timeout/RSS controls, preserve execution/identity and require explicit elevated correspondence replay allowances; verify direct consumers.
- [x] F.2 Bind type-text rows and generation metadata to one read transaction; reject a generation change after validation and preserve legacy freshness-policy labels.
- [x] F.3 Deliver a short TeX-plus-theorem recipe in docs and both skills, with statement/method distinctions and incomplete-manifest scope.
- [x] F.4 Provide a focused generation-freshness observation with phase timings and no historical database hashing; test edits, expected-generation mismatch and unavailable input.

The owner subsequently selected removal of automatic archives over retention
rotation; H.1–H.3 above own that next work. The current optional history cap stops
growth; it does not rotate history. Existing archives remain until an explicit
catalog-aware cleanup is applied. F.1–F.4 do not implement that cleanup.
The historical eleven unchecked tasks remain superseded and unmet.

**Internal release qualification complete — 2026-11-17.** See
[0.4.3 verification](../../../docs/releases/0.4.3/verification.json) for the
isolated installed/Lean gates, complete original suite and passing fixture
corrections, clean static quality, and preserved evidence. The original suite
is not relabeled green; its three stale-fixture failures and 11-test correction
run remain separate. No production change followed installed qualification.
The next work is internal consumer feedback, not another automatic audit.

**Internal 0.4.3 consolidation — 2026-11-17.** R.1–R.5 and the native
correspondence-context child (12/12) are complete. The user adopted consolidation
and internal handoff. The original three-diagnostic integration/full-scorer
roadmap is **superseded as an investment plan**. Its eleven unchecked acceptance
tasks below remain unmet historical requirements, not release blockers or an
automatic queue. Preserve their corpus, results, unresolved cases and saturated
feasibility gate; this release cannot retroactively satisfy that gate.

The delivered next step is ordinary internal use with exact feedback: source
question, chosen interpretation, query/evidence, unresolved scope and effort.
A reproduced tool failure or repeated missing operation may justify a narrowly
scoped change. Broader ProofIR expansion or another comparison needs a new
explicit hypothesis and decision. Release qualification is recorded in
[0.4.3 notes](../../../docs/RELEASE_0_4_3.md); it is separate from historical
mathematical acceptance. Completed evidence directories stay in place so frozen
receipts and cross-repository references retain their paths.

**Receipt history — r04 received 2026-11-17, initially pending validation.** The user
supplied `temp/ladon-semantic-strategy-review-r04.zip`, reviewing the r04 source
packet identified below. Received claims: two generated-goal diagnostic returns
lose the origin marker needed to hash large captured inventories; substantive
check telemetry counts object-map typing; wrapper boundaries obscure packaged
assumptions and the Adam source anchor needs surrounding context. The review
retains conditional f-DP refutation and the absence of measured discovery/value
advantage. Recommendation: a bounded diagnostic/telemetry consolidation and a
real reader handoff; definition delivery only if a reader encounters a concrete
lookup problem. Next: inspect and identify the bundle, reproduce code findings,
check mathematical/attribution and cost claims against retained evidence, then
reconcile proposal/design/spec/tasks. All claims are received, not yet accepted;
no fresh experiment, proof replay or broad ProofIR expansion is authorized by
the review itself. Historical evidence and completed native qualification remain
unchanged.

**Reconciled 2026-11-17:** [r04 dispositions and reproduction](evidence/pro-review-r04/RECONCILIATION.md)
accept F01–F04 within their stated boundaries and retain F05's authority limits.
The 705 bundle hashes, 79 isolated code assertions, 384 finite privacy checks,
eight retained check records and cost ledger pass. Probed production sources
match the checkout. No fresh Lean replay, full test run, code edit or reader
experiment was performed. Review ZIP SHA-256:
`a3a743eaebaced4f631077e59b053ea534b955edea41ffd7e2642310cea1ea09`.
The review is now received; the preparation entry below is historical.

### R: r04 consolidation and actual reader handoff

This package is complete. It does not reopen the historical integration
roadmap or the completed 12/12 native-context qualification. R.2 and R.3 are
bounded repairs; R.4 prepares actual internal use, not a fresh discovery score.

- [x] R.1 Record and reconcile the received review, reproduce diagnostic/telemetry findings, verify retained mathematical/cost claims and preserve all prior evidence. See [reconciliation](evidence/pro-review-r04/RECONCILIATION.md).
- [x] R.2 Fix generated-obligation failure recording. Reproduce both early `_check_goal` diagnostics through the real branch and artifact producer with bounded I/O fixtures; retain unresolved verdicts and exact origin. Cover 10,001 and 32,768 modules, rejection at 32,769 and unchanged unrelated-list/byte limits. Inspect other capture-bearing exits. No fresh large Lean run is required unless these tests expose a runtime uncertainty.
- [x] R.3 Correct role reporting and selected-premise scope. Test separate typing/map/replay/premise/transfer roles, actual attempted counts and zero-direct-premise scope. Keep packaged source assumptions explicitly unaudited unless separately reconciled; preserve support semantics and frozen telemetry. Add an append-only Adam source-context clarification using the original clock, initialization, query, diffusion and uniqueness passages; check exact lines/hashes and describe common law per input. Update the reader guide and relevant CLI/report consumers with compatibility checked.
- [x] R.4 Prepare and observe one actual internal reader handoff using the existing guide and a selected consequential MF question. Record consumer/task, prior exposure, exact source and evidence identities, first interpretation, formal meaning, assumptions, conclusion, unresolved scope, evidence used and available costs/failures. Use stored inspection when sufficient. Keep reviewer answers separate from initial reader inputs; do not contact anyone or launch agents solely on this task's existence.
- [x] R.5 Record the handoff decision. If navigation works, consolidate. If retrieval is the demonstrated obstacle, prototype bounded definition delivery through existing owners/source maps/attachments with explicit frontier and byte/declaration limits. If accessible definitions still yield wrong interpretations, prioritize reconciliation. A comparison or new representation requires separate declared scope and evidence; no automatic campaign follows.

**R.2 verified:** real diagnostic branches and artifact production pass at the
recognized inventory bounds (32 focused tests); other collection/byte limits remain.
**R.4–R.5 complete:** [internal reader decision](evidence/r04-reader-use/DECISION.md)
correctly rejects reuse of the old common-law certificate for the newer finite
batch comparison while retaining its actual conditional support. Existing
navigation sufficed; no definition feature or comparison is justified here.
**R.3 complete:** [implementation and verification](evidence/r04-consolidation/REPORT.md)
records corrected role accounting, explicit premise scope and append-only source
context. The then-current integration run had 180 passes and one pre-extraction
failure because `tests/test_correspondence_real_application.py` required an absent
external Navier–Stokes checkout. At the user's request, that test file was removed
on 2026-11-17; the historical run output remains unchanged. The 180 passing
results are preserved. Changed-file strict quality and repository lint passed;
that checkpoint retained ten global complexity findings in unchanged
real-bound files. The subsequent 0.4.3 helper-only refactor resolves those static
findings; the release notes own its separate qualification. All R tasks are complete within scope. This is one internal
consumer exercise, not measured product advantage; the broader gates are not green.

The proposed five-day ceiling remains advisory, not a newly adopted budget.
R.4 found ordinary navigation sufficient; no production definition view follows. See [design](design.md#r04-consolidation-and-reader-decision).

**Historical review handoff — r04 requested (2026-11-16):** prepare a new revision
of `temp/ladon-semantic-strategy-review-data-r04.zip` covering the completed native
MF qualification, inventory serialization repairs and consolidated reading recipe.
Ask for the big picture and a concrete next investment decision, including whether
the wrapper-based checks provide substantive audit value. Preserve r03 and all
frozen evidence; no r03 response has been received. Packet preparation alone
launches no experiment or further implementation. Status: source-first r04 packet prepared; current decision and included evidence
are described in its README and REVIEW_PROMPT. Validation and archive identity
are recorded in packet-local `data/validation-summary.json` and `data/revision.json`.
Earlier review archives remain preserved; the r04 response is pending.
Prepared archive: [r04 ZIP](../../../temp/ladon-semantic-strategy-review-data-r04.zip),
[review prompt](../../../temp/ladon-semantic-strategy-review-data-r04/REVIEW_PROMPT.md).
383 files; 371 copied-source hashes and 150 retained-manifest entries verify;
eight strict OpenSpec validations pass. ZIP integrity/JSON/hygiene and authored
entry links pass. Archive size 20,205,804 bytes; SHA-256
`ce9999771e8c2cfaa75b967936db97035ea961440a21ef04d4a5d63f41e0577a`.
The packet binds the preparation snapshot before this final archive receipt;
original runs/tests are reported evidence, not rerun during packaging. No reviewer
contact, new mathematical run, commit or push occurred during preparation.

Reviewed 2026-11-17. This section owns current program status; dated sections below
preserve milestone history. The objective remains useful mathematical auditing,
with exact source interpretations, checked obligations and honest coverage.

| Workstream | Delivered | Remaining boundary |
| --- | --- | --- |
| Original pitfall corpus and children | Reviewed 24-case corpus; accepted four-case feasibility and four-case provenance baselines. | Sixteen cases unmeasured; no accepted integrated feasibility/provenance/operation-property stages. The [baseline ledger](../ladon-pitfall-baselines/tasks.md) owns exact outcomes, including the unsupported selector. |
| Real-source findings | [PLD reconstruction sign error](../ladon-pld-core-source-audit/evidence/pld-core-r03/REPORT-v2.md), independently upheld; later bounded sibling repair. | Broader PLD probability-law/formal correspondence is incomplete. Source reasoning established the finding; no distinctive Ladon detection gain was measured. |
| Checked-application workflow | M.1–M.3, S.1–S.3 and N.3: premise routes, supplied witnesses, consistent source-context applications, alternative proofs and conclusion controls. Guide and skill recipes; native printer, heartbeat and auxiliary-export fixes qualified on retained failures. | These qualify selected operations and exposed cases, not automatic prose interpretation or general pitfall detection. |
| ProofIR evidence delivery | [Correspondence-context packet](../ladon-proofir-correspondence-context/tasks.md) complete (12/12): exact source/formal context, stored target bindings, exposed controls and eight native MF checks; [reusable reading recipe](../../../docs/PROOF_CORRESPONDENCE_AUDIT.md#read-the-native-mf-examples). | Source interpretation remains attributed; named predicates require definition review. No fresh detection or reader-benefit result. |
| Comparisons | Six-claim matched pilot, five-unit synthetic comparison and two-unit application diagnostic completed; scoring corrections preserved. | No incremental detection or measured effort benefit. In the synthetic comparison assisted found one of two faults, control both; false reassurance remains a central risk. |
| DP-Adam consumer | U.1–U.6; [general source-family construction, common-law and privacy/utility applications](evidence/dpadam-source-constructor-r01/REPORT.md), plus documentation consolidation. | The broader 558-line source-method audit is unfinished; no uniform finite-run rate or transfer of Malladi's simultaneous beta changes was established. |
| f-DP consumer | U.7 bounded support audit, ordering controls and [finite privacy countermodel](evidence/fdp-ordering-privacy-20261115T072023Z/REPORT.md). | The inherited-order claim is refuted; the manuscript's intended ordering remains unresolved. A shuffled control on one pair is not a general repaired theorem. |

U.1–U.7 are complete as scoped investigations. Before r04 reconciliation the CLI
counted 32/43 umbrella tasks complete; its eleven unchecked tasks belonged to
historical broad integration/acceptance. R tracks five bounded consolidation/reader tasks separately from those historical
requirements; its current checkboxes above own progress. The completion fraction
does not measure mathematical coverage or product reliability. Those requirements
remain unmet historical acceptance; their investment sequence is superseded,
not retroactively passed. The original
feasibility improvement gate has no headroom on its frozen faults; finishing its
scorer cannot satisfy that gate.

**Completed pre-r04 sequence; R above owns the current next actions:**

1. **Complete:** Resolve the f-DP source interpretation or deliver a conditional
   clarification if local definitions cannot settle it. Completed: [source
   interpretation](evidence/fdp-source-interpretation-r01/INTERPRETATION.md)
   records that the map from uniform subsets to ordered inputs is unspecified,
   with exact source lines and hashes. The checked result is conditional on
   inherited increasing order. Do not attempt to prove that refuted target.
   Any repaired theorem needs its own sampler/assumption; a general shuffled or
   permutation-invariant theorem is not a prerequisite for Ladon work.
2. **Complete:** Consolidate the finding into the existing object-map/countermodel recipe and
   a compact exposed worked example. Verify that the example checks the original
   mechanism's assumptions and actual released law, and explains its conditional
   source verdict. The [worked example](../../../docs/PROOF_CORRESPONDENCE_AUDIT.md#worked-example-hidden-fixed-size-f-dp-subsampling)
   was checked against the exact finite countermodel and source interpretation.
   This is guidance/regression material, not a fresh detection score or a reason
   to build a paper-specific runtime adapter.
3. **Decision recorded:** Reuse the recipe and pause semantic runtime expansion.
   The completed comparisons show no incremental detection or measured effort
   gain, and no repeatable missing operation has been demonstrated by this case.
   A future comparison needs a concrete prediction, fresh registered inputs, the
   same recipe in both arms, and false-reassurance/false-accusation and cost
   endpoints. No broad benchmark, full DP-Adam audit or Navier–Stokes rerun is
   queued here.

MF remains a read-only donor for this Ladon work. Source clarification can be
staged locally; donor repairs are separate work. Frozen reports and manifests
retain their original outcomes, failures, authority limits and timing.

## Reflection and continuation criteria — 2026-11-15

**External review r03 requested — 2026-11-16:** prepare
`temp/ladon-semantic-strategy-review-data-r03.zip` as the next revision of the
semantic-strategy review. Primary decision: which improvement, if any, should
follow the new ProofIR inspection and mathematical controls. The packet must
include negative comparisons, false-reassurance evidence, current source/code,
conditional real findings and checking/interpretation limits. Ask for a big-picture
assessment, a prioritized bounded work package, a falsifiable evaluation and
consolidation/stop alternatives. No additional implementation or experiment is
launched by preparing the packet. The review has not yet been received.

Preparation complete: [r03 archive](../../../temp/ladon-semantic-strategy-review-data-r03.zip)
and [review prompt](../../../temp/ladon-semantic-strategy-review-data-r03/REVIEW_PROMPT.md).
The source-first archive contains 294 files (4,292,068 compressed bytes), including
current ProofIR code and exact controls, negative comparisons, corrected scoring,
real-source evidence and six author entry points. All 282 copied-source hashes,
80 selected retained-manifest entries, strict JSON and eight OpenSpec validations
pass; archive bytes/hygiene and entry-point links verify. This is not a complete
MF/Mathlib or Python runtime closure; no new Lean replay, experiment, or bundled
script execution occurred during packaging. SHA-256:
`35d419f69e19c982ae32d425806c3ae94a9be7215bccf1f232994040a0b49d6f`.
The packet preserves a source-note hash transcription error with an append-only
correction. No reviewer was contacted and no recommendation is accepted yet.

**Authorized ProofIR follow-up:** the user selected ProofIR improvement after this
reflection. The bounded [correspondence-context packet](../ladon-proofir-correspondence-context/tasks.md)
addresses a reproduced inspection gap: stored source interpretation and formal
slice were absent from the native correspondence query. It reuses existing
records and does not reopen the three-child integration roadmap. Its own ledger
records completed implementation, public CLI qualification and focused checks;
improved detection remains unmeasured.

The 2026-11-16 continuation found that exact checked targets survive in existing
receipt extensions but were hidden behind inspection references. The same packet
now exposes these targets and compares stored obligation/plan/polarity bindings,
including explicitly unbound non-open obligations. Its ledger owns qualification.
This is a consistency diagnostic on stored evidence; direct mapping dependencies
remain a separate inspected boundary, and no detection advantage is inferred.

The subsequent [three exposed mathematical controls](../ladon-proofir-correspondence-context/evidence/mathematical-controls-r01/REPORT.md)
completed nine native replayed checks: faithful support, refuted mapping of an
identical true source claim, and a refuted quantifier transfer with a separately
checked source refutation. Existing map/formula/closed-target records preserved
the distinctions. Consolidate the reading recipe; this qualification supplies no
new graph requirement, fresh reader-benefit result or detection score.

**Assessment:** the package has delivered useful mathematical audits, a reusable
checked-application workflow and repairs to demonstrated tool failures. It has
not delivered the three integrated semantic diagnostics or demonstrated an
incremental detection/effort advantage. The research direction has substantive
positive evidence; the software investment hypothesis remains unproven.

### What the evidence taught us

1. **The semantic gap is real, and local audits can expose it.** The independently
   upheld PLD sign error is a source-formula finding. The later f-DP countermodel
   refutes one explicit ordering interpretation; the source's intended map remains
   unspecified. These are different strengths of conclusion. Neither is evidence
   that Ladon automatically discovered a faulty Lean theorem.
2. **A premise list must constrain the verdict.** Synthetic unit 03 received the
   missing formal premise and nevertheless reported support. The checking target
   is one application under the source assumptions, with a consistent object map
   and conclusion transfer. A filled ledger or replay of the original conditional
   theorem cannot substitute for that application. Fresh prevention of this
   failure remains unestablished.
3. **Object construction is part of the mathematics.** DP-Adam required actual
   family records and their common law; f-DP required a subset-to-tuple map and
   the resulting released law. A missing bridge may conceal a false claim or
   require genuine mathematics. Try a small countermodel where appropriate before
   investing in a large proof or extraction; check all original premises and the
   failed conclusion before crediting it.
4. **Checking and discovery are separate achievements.** Native replay/trust
   checks and ordinary Lean establish their exact supplied judgments. Selecting
   the obligation and validating its prose interpretation remain attributed
   work. The comparisons have not shown a Ladon advantage; their small, prepared
   populations and incomplete cost accounting also do not prove that every
   proposed diagnostic would be ineffective.
5. **Operational reliability and honest stopping matter.** The printer,
   heartbeat and auxiliary-export repairs addressed retained failures. The
   DP-Adam stop correction showed that a controller can faithfully report
   unjustified authored blocker labels. Evidence machinery does not certify the
   judgment that unperformed review is blocked or that an audit is complete.

### What to do next, and why

The 2026-11-16 user-selected continuation now has
[native MF qualification evidence](../ladon-proofir-correspondence-context/evidence/mf-native-r01/REPORT.md).
All eight supplied-proof obligations passed replay/trust: the inherited-order fDP
conclusion transfer is refuted, and the DP-Adam common-law interpretation is
supported. Both public inspections expose complete context and matching target
bindings. The previous [ordinary-evidence trace](../ladon-proofir-correspondence-context/evidence/mf-trace-r01/REPORT.md)
remains historical; native production is no longer missing for these selected
wrappers. A reproduced module-inventory serialization cap was repaired without
changing replay authority or canonical identities. Final checks took roughly
8.3/7.5 minutes under the user-authorized 1800-second timeout and unchanged
12-GiB cap; all failed attempts remain recorded.

Consolidation is complete: the [native MF reading recipe](../../../docs/PROOF_CORRESPONDENCE_AUDIT.md#read-the-native-mf-examples)
provides verified local CLI commands and qualified source verdicts. Both commands
reproduce the retained inspections exactly; custody verification and all 70
manifest hashes pass. Use the pending r03 review or a concrete internal reader
question to choose further investment. No new relationship loss or fresh detection gain
was established. Source interpretation remains attributed, DP-Adam's named
predicate requires definition inspection, and whole-paper audits remain open.
These results do not alter the already frozen r03 review archive.

Beyond this selected exposed qualification, use an actual internal reader question with the consolidated
[audit recipe](../../../docs/PROOF_CORRESPONDENCE_AUDIT.md), when such a question
arises in normal work. The original reflection selected no additional run; the
subsequent user selection above now owns the immediate continuation.
This tests usefulness where the user needs an answer and avoids treating the
remaining historical checklist as an automatic implementation queue.

For that use, retain the source-only interpretation before candidate exposure
where possible, disclose prior exposure, and identify the exact supported or
unresolved application. Record what changed for the reader, which operation Ladon
contributed, failures, and available preparation/checking/review effort. Missing
telemetry remains missing. An informed field report is useful feedback without
being a comparative experiment.

| Feedback | Next action | Required boundary |
| --- | --- | --- |
| Existing recipe and tools answer the question | Reuse and consolidate the recipe. | Do not infer a measured software advantage from one successful audit. |
| Reproduced tool failure prevents an otherwise valid check | Qualify the smallest general fix on the retained request. | A missing mathematical proof is not a software failure. |
| The same manual operation repeatedly loses scope, object identity or evidence, or incurs measured cost | Propose a narrow capability with a concrete expected improvement. | Explain what existing commands cannot supply and preserve their checking authority. |
| A concrete comparative prediction is ready | Register a small fresh comparison with the same recipe in both arms. | Include useful findings, false reassurance, false accusations, justified support, abstention and total effort; freeze the practical success threshold before running. |
| No such need or prediction is available | Keep semantic runtime expansion paused. | Do not launch another broad campaign merely to seek a positive score. |

The three diagnostic children remain candidate capabilities with unmet acceptance,
not promised next deliverables. The full scorer and all-child integration retain
their historical contracts; completing them is not the current investment plan.
Neither new field evidence nor a new comparison can satisfy the saturated old
feasibility gate retroactively. This review changes no checkboxes or frozen results.

## Completed consumer audit U.7 and mathematical follow-up

**Latest mathematical result — 2026-11-15:** [the finite countermodel](evidence/fdp-ordering-privacy-20261115T072023Z/REPORT.md)
refutes the classical amplification bound under the explicitly inherited-order
sampler. The base mechanism satisfies all original finite-domain privacy and
real randomized-test obligations; the hidden sampled event exceeds the claimed
factor-5/3 bound by 1/54. A shuffled-order control passes for the same pair.
This supersedes attempting to prove the inherited-order branch of the handoff.
The manuscript's intended ordering remains unresolved, so no unqualified paper
refutation is claimed. Next resolve source sampler/dataset semantics, then select
a matching theorem or separately labeled repair. Existing MF sources and frozen
audit records remain unchanged. This is exposed mathematical development evidence,
not a measured Ladon detection gain or new runtime-feature requirement.

U.1–U.7 are complete within their stated investigation scopes. U.7 assessed the
exposed f-DP reserve and delivered unresolved formal support with an exact
mechanism-to-testing obligation. The report below owns the outcome. The
[consumer-audit recipe](design.md#consumer-audit-recipe-u7) is retained for reuse.
Do not begin with the historical unchecked tasks in sections 1–4 below.

For a future use of the recipe, the caller supplies one source claim, or explicitly selects the exposed f-DP
reserve described in the recipe. No new audit is launched by this plan revision.
The work is suitable for one Luna-medium agent; the recipe requires no swarm or
independent-review claim. An agent that cannot discharge a difficult bridge
returns the exact remaining obligation and evidence, not an invented proof.

Historical launch template (U.7 is complete; this is not a request to rerun):

> Apply U.7 in `openspec/changes/ladon-semantic-pitfalls-umbrella/tasks.md` using
> the consumer-audit recipe in `design.md`. Select the exposed hidden fixed-size
> f-DP reserve. Use this Ladon checkout and treat matrix-factorization as
> read-only. Use a fresh run directory and the recipe's existing field-exercise
> bounds. Deliver the interpretation, exact application or residual, evidence,
> and short reader-facing report. Do not implement runtime features or edit donor
> mathematics. Stop at the declared bounded assessment and update U.7's ledger.

- [x] U.7a Freeze the selected reader question and source interpretation using recipe steps 1–2. Verify source paths/hashes, runtime identity and a fresh output directory; deliver `INPUTS.json` and `INTERPRETATION.md` before candidate checking. Preserve ambiguity and disclose prior exposure.
- [x] U.7b Follow recipe step 3 to identify a candidate route and its actual object/assumption map. Deliver `APPLICATION.md` with the exact source judgment, inspected owner signatures, derived premises and residuals. For the f-DP reserve, settle or explicitly retain the source adjacency ambiguity before asserting an exact matching theorem.
- [x] U.7c Follow recipe step 4 to check the decisive application or make a bounded attempt at the missing bridge. Retain commands, failures, compiler/axiom or native replay/trust outcomes and time to substantive evidence. A checked residual or precise unresolved route completes this investigation task, not the mathematical theorem; name any unattempted obligations separately.
- [x] U.7d Apply the decision table and report template in recipe step 5. Deliver `REPORT.md`, `COSTS.json` and a file manifest; verify every support/refutation statement against exact evidence and every original claim against the coverage ledger. Explicitly distinguish tool failures, missing mathematics and interpretation ambiguity. Do not credit an empty residual list or controller stop alone.
- [x] U.7e Reconcile this current-state paragraph, U.7 checkboxes and the linked report; run strict OpenSpec validation and check new links. Recommend consolidation, one evidence-backed tool fix, or a specifically scoped mathematical follow-up. Do not automatically launch another audit or mark historical acceptance gates passed.

**U.7 status:** completed as a bounded informed audit: [report](evidence/pitfalls-consumer-fdp-20261114T131246Z/REPORT.md).
The user's continuation selected the prepared reserve. Surrounding source inspection
resolved replace-one adjacency; ordinary Lean checked the actual definition and a
consistent conditional scalar application. Full arbitrary-mechanism support stays
unresolved: the inspected routes do not construct the hidden marginal output laws
and derive the testing-error feasibility constraints and C_p conclusion from them.
Both Lean attempts passed with standard axioms; the report records costs, direct
input identities and limits. At the U.7 checkpoint no source fault or tool failure was established; the later conditional counterexample is recorded above.
A [staged MF follow-up handoff](evidence/fdp-mechanism-followup-r01/HANDOFF.md)
now specifies the interpretation, hidden-law, testing-error and conclusion gates,
existing owners, controls and stop rules. It is retained in Ladon; MF remains
read-only. The inherited-order proof branch is superseded by the later countermodel;
other readings require their own source justification. This is mathematical work,
not an evidenced need for a new Ladon detector.

**2026-11-15 interpretation clarification:** the source fixes replace-one adjacency
but does not explicitly fix the subset-to-tuple ordering. U.7's inherited-order
choice remains an attributed reading, not a source-certified requirement. Gate A
of the handoff requires validating that choice or reporting conditional readings;
subset replacement need not preserve coordinate adjacency of sorted tuples.
The original U.7 evidence remains unchanged, and its unresolved-support verdict
still holds. A general mechanism bridge may require substantial mathematics;
calling it an adapter does not establish its feasibility or cost.

**Gate A continuation:** [the checked ordering assessment](evidence/fdp-ordering-gate-a-20261115T012614Z/REPORT.md)
completed the handoff's interpretation assessment, retaining the source ambiguity.
Generic injective-selection and in-place replacement lemmas compile, and a finite
control shows increasing versus shuffled ordering yields different observable
laws for an order-sensitive mechanism. Sorted subset replacement can change two
tuple coordinates. That checkpoint established a representation/control result; the later privacy
countermodel strengthens it. One failed draft and the successful ordinary Lean receipt are
retained. For a separately justified, unrefuted reading, Gates B–D remain open:
source-policy justification, hidden-law/coupling
construction, original-premise production and full C_p conclusion transfer. A
conditional ordered-injection route can reuse the lemmas but cannot claim source
equivalence without its own justification. No new runtime diagnostic is warranted.
Historical acceptance gates below remain deferred and unmet.

## Historical internal-use checkpoint — 2026-11-14

Internal 0.4.2 feedback: [r01](evidence/internal-0.4.2-adam-energy-r01/REPORT.md)
completed the Adam energy ceiling, and [r02](evidence/internal-0.4.2-adam-energy-r02/REPORT.md)
checked the full chain in ordinary Lean while retaining native heartbeat failures.
The [U.1 remedy](evidence/completion-heartbeats-r01/REPORT.md) now completes the exact
full-chain term natively with default resources: application, round-trip, replay and
standard trust all accepted. Completion defaults to 800,000 configurable heartbeats and
exports generated auxiliaries for replay. The full completion suite passes 62/62.
Source mapping remains inspected and included an attributed root correction. No source
fault or incremental detection gain was established. The subsequent [DP-Adam field record](evidence/dpadam-batch-pair-r01/REPORT.md) delivered U.2–U.4 as an informed root exercise; the [review correction below](#review-of-the-dp-adam-field-record) qualifies its stopping claim. It checks an actual sampled quadratic batch pair and a native privacy cancellation, and U.5 subsequently delivered a general family construction and consumer composition. The original broader source-method audit remains unfinished. Consolidate the existing recipe; no new runtime feature is justified. Broad diagnostic integration and historical detection gates stay deferred.

- [x] U.1 Diagnose the [retained Adam full-chain native heartbeat failure](evidence/internal-0.4.2-adam-energy-r02/REPORT.md) with an isolated helper experiment identifying the failing phase/accounting boundary. Qualify the smallest finite resource-control remedy through the existing public completion route, with default compatibility, invalid-option, exhaustion, replay/trust and stale-context checks as applicable. Preserve candidate-generated auxiliary declarations in the private replay environment, and verify that generated axioms remain trust-rejected. Recheck this exact term; standalone Lean success does not close native acceptance. Preserve all prior failed/successful records. Completed: [diagnosis, implementation and default-resource native acceptance](evidence/completion-heartbeats-r01/REPORT.md).

## Completed milestone — internal-use feedback

U.1 closes the demonstrated native Adam blocker. U.2–U.4 used the corrected local Ladon checkout on the user-selected DP-Adam batch-scaling question from ongoing matrix-factorization work. This is an internal field exercise, not a new scored comparison or a rerun of the accepted Adam request. The [field-use contract](design.md#internal-use-feedback-after-u1) owns the procedure and evidence boundary.

- [x] U.2 Prepare one bounded consumer handoff. Select the next real claim with its source definitions and pinned Lean environment; state the reader question, source spans, known exposure/crosswalks, finite execution bounds and output location. Verify that the invocation resolves to this Ladon checkout including U.1, not the globally installed package. Include the existing checked-application recipe and public command examples. Completion is a runnable handoff with an explicit full source goal and recording instructions, not a claim that the mathematics is already supported. Completed: [informed consumer handoff and source/runtime scope](evidence/dpadam-batch-pair-r01/HANDOFF.md). The root acted as the consumer; no fresh-agent claim.
- [x] U.3 Collect the consumer's field-use evidence. Preserve the first attributed interpretation and revisions, original assumptions, consistent object map, application and conclusion-transfer obligations, commands and exact input/runtime identities. Record completed support, a separately justified refutation, or explicit residual obligations; distinguish ordinary Lean evidence from native completion/replay/trust. Record time to a substantive query and interpreted result, setup/checking/review effort and observed resource stops; unavailable telemetry stays unavailable. Preserve failures and explain what the evidence changes for the reader. Completion permits an unresolved mathematical result with a precise remaining obligation. Completed: [DP-Adam batch-pair evidence](evidence/dpadam-batch-pair-r01/REPORT.md). Native privacy cancellation accepted; ordinary Lean checks actual sampled quadratic families, common limiting law, matched-epoch step scaling, eventual privacy and a common finite-iterate bound. General source-to-family construction remains unverified.
- [x] U.4 Triage the feedback and close this field exercise. Identify what Ladon actually contributed and whether the difficulty was interpretation, mathematical proof, evidence access, invocation or resources. Reuse the existing recipe when it suffices; propose a narrowly scoped fix only for a concrete reproduced tool failure. Record a consolidation/fix/pause decision and any exact follow-up obligation. One field exercise cannot establish comparative detection or effort advantage, close a historical gate, or automatically launch another campaign. Completed with the [review correction](#review-of-the-dp-adam-field-record) to the original [disposition](evidence/dpadam-batch-pair-r01/REPORT.md#disposition). No production blocker or default change was demonstrated. The general primitive-to-two-family bridge is a mathematical follow-up, not automatic detector work.

## Review of the DP-Adam field record

Current-session root review, 2026-11-14; not independent review. The retained proof bodies supply the sampled quadratic construction, a common named path law via solution uniqueness, and actual finite-mechanism privacy/retained-iterate utility applications. No mathematical defect was found in those new proofs. All 56 evidence-manifest entries, both final proof-source hashes and listed donor source/direct compiled-import identities matched. The native receipt reports completed replay and accepted standard axioms. This review inspected existing receipts; it did not rerun Lean or validate a transitive dependency/source-build closure.

**[P2] Correct the interpretation of the source-audit stop.** The frozen [plan](evidence/dpadam-batch-pair-r01/plan-01.json) labels 21 groups `missing-reviewed-support`. At least `adaptive-transfer`, `runtime-rescaling` and `scope-small-budget` describe work not performed, without evidence preventing that work. The [terminal receipt](evidence/dpadam-batch-pair-r01/terminal.json) was emitted after 1,214.38 seconds with 1,185.62 seconds remaining. A read-only review using `ladon.investigation.assess`, the original receipt's elapsed time, and an in-memory copy returning just those three groups to `contract` produced `continue`, three actionable items and `mayFinalize=false`. This is a retrospective classification check, not a replacement receipt or a new audit run.

Preserve the original plan, report, receipts, clock and manifest. The CLI correctly reflected its authored labels; it did not verify their justification. The earlier report's claim that this was an evidenced all-blocked stopping point is not accepted by this review. The current conclusion is **partial mathematical support with unfinished source review**. Do not convert that historical stop to budget exhaustion merely because time has since passed. Do not treat the other 18 blocker labels as reviewed/accepted by subtraction.

U.2 and U.3 retain their delivered handoff/evidence status, and U.4's disposition is corrected here: consolidate the successful checking route, preserve the incomplete original investigation, and continue only the original mathematical support question below. Their completion denotes delivery and triage of a partial field record, not valid completion of the 558-line source audit. No production detector or extra runtime enforcement is requested by this correction.

## Completed mathematical step — recover the original batch-pair application

- [x] U.5 Resolve the source-to-family support frontier of the original DP-Adam batch-pair question. Follow the recipe below before writing a new constructor. Completion is a source-bound paired application with conclusion transfer, or a bounded unresolved assessment naming a concrete remaining obligation and the attempted route; a repeated scalar identity, another quadratic control, or an unperformed review labeled blocked is insufficient. Keep native and ordinary Lean authority separate. Do not certify the whole manuscript or transfer Malladi's simultaneous beta changes.

Completed U.5: [general constructor and consumers](evidence/dpadam-source-constructor-r01/REPORT.md). Ordinary Lean constructs arbitrary-query families, rebuilds release measurability, proves the common named law after resampling, and applies actual finite privacy and empirical-objective retained-iterate utility. The empirical gradient premise is derived from record losses and composed into the utility application. A checked objective-field irrelevance lemma removes the speculative `SmoothObjective` packaging dependency; the real utility objective remains explicit. This closes the bounded application frontier, not the original unfinished 558-line source-method audit. No mathematical fault or Ladon-specific detection gain was established. Consolidate; no broad runtime stage, rerun or new campaign follows automatically. The earlier [fixed-query/initialization bridge](evidence/dpadam-general-bridge-r01/REPORT.md) remains a historical partial result.

The recipe below records the completed U.5 procedure and is not a request for another run.

- [x] U.6 Consolidate the U.5 lessons into the existing audit guide and bundled/shared Ladon skills: actual record construction, normalization/indexing, checked field irrelevance, consistent conclusion transfer, and eventual-versus-finite guarantees. Deliver a short worked-example entry point with read-only receipt inspection; verify its commands and links without rerunning the mathematical audit. Completed in [the object-construction recipe and DP-Adam example](../../../docs/PROOF_CORRESPONDENCE_AUDIT.md#construct-the-objects-behind-a-theorem-application), the bundled skill, and shared `ladon/references/proofir-and-correspondence.md`. This is documentation consolidation, not new detection or proof evidence.

Historical U.6 disposition: select a real consumer question using the consolidated workflow. U.7 subsequently selected the f-DP reserve; the current status above owns its outcome and follow-up. The separate [MF finite-horizon batch-scaling packet](../../../../lean/matrix-factorization/openspec/changes/dpadam-finite-horizon-batch-scaling/proposal.md) strengthens mathematics under its own assumptions and is not a Ladon prerequisite. The original broader source-method audit remains incomplete.

U.6 validation: the guide's read-only command verified all 40 general-construction manifest entries and the final proof/receipt source digest, then displayed the retained compiler outcome. New example links resolve; both bundled and shared skill validators, scoped whitespace checks and strict OpenSpec validation pass (existing requirement-length advisories only). No new Lean run or independent review was performed.

1. Reuse the original [reader question](evidence/dpadam-batch-pair-r01/HANDOFF.md) and disclose prior exposure. Bind the exact passage and assumptions; the selected passage is the diffusion manuscript, not an unidentified broader report claim. Declare any new bounded continuation separately while retaining the original unfinished investigation and its timing.
2. Inspect existing producers of `GrowingClockData` and their consumers before proposing new mathematics. For the same dataset, fixed queries, clipping, beta, initial limit and public bounds, map both q and kq schedules to actual families. Identify which fields are supplied by the source, derived, or not yet discharged. An unsuccessful name search does not establish that an adapter is absent.
3. Check the highest-risk missing connection first: arbitrary source queries/initialization to the formal family data, including release measurability, the nested initial-condition fields and local clipped-mean coherence. A generic conditional comparison of already-supplied records remains partial support. Add only a small local composition if existing producers suffice; do not start a general framework or duplicate an owner.
4. Join the two consistent applications to common horizon/initial state, drift, driver covariance and the same solution law; then account separately for eventual privacy and the retained-iterate utility conclusion. Preserve fixed beta, admissible counts, matched rather than constant epochs, and lack of a uniform finite-run rate. Do not assume the desired common law or utility in a new record field.
5. Keep unreviewed work actionable unless a specific evidenced dependency or authorized scope boundary prevents it. Record legitimate bounds/stops as they occur; no retrospective clock reset, idle deadline expiry or blanket blocker conversion. At disposition, explain what changed for the mathematical reader and whether any actual Ladon failure was encountered. Broader diagnostics stay deferred.

The [hidden fixed-size f-DP subsampling map](evidence/fdp-subsampling-map-r01/REPORT.md) is a reserve mathematical follow-up if the consumer has no better current claim: inspect whether the actual mechanism, output laws and trade-off conclusion can be joined under the source assumptions. Its missing inspected bridge is unresolved support, not an established fault. The [Gaussian mechanism screen](evidence/gaussian-mechanism-map-r01/REPORT.md) is not yet a validated positive control. Navier–Stokes remains a later isolated known-fault regression. No new detector, capsule campaign or full-paper audit is required by U.2–U.4.

The objective remains useful mathematical detection: determine whether a source claim is supported under its actual assumptions, identify a concrete discrepancy when there is one, and explain the evidence to a reader. This ledger owns the umbrella's current sequencing; child ledgers own their detailed acceptance. Completed audit packets do not close the three planned production diagnostics.

| Workstream | Established evidence | Still open / disposition |
| --- | --- | --- |
| Article-inspired corpus and baseline | All 24 cases were reviewed and validated as fixtures; eight cases have accepted operational baseline records across feasibility and provenance. | Sixteen cases unmeasured. One accepted provenance outcome is unsupported, so eight accepted records do not mean eight successful detections/controls. See [baseline tasks](../ladon-pitfall-baselines/tasks.md). |
| Assumption feasibility | Declaration-level closure prototype and supplied-term controls; four accepted supplied-proposition baseline outcomes. | Actual proof-position context reconstruction, fixed assignments, dependency-preserving closure and public stage remain unimplemented/unaccepted. U.1 fixes generated-auxiliary replay in the shared completion route; the feasibility prototype needs its own qualification before that child blocker is closed. |
| Premise provenance | DP-SGD actual-use observation; reviewed M.1–M.3 comparison with one constructed omission and three controls. | General scoped-route API and independent provider replay remain open. Existing observations do not establish premise necessity or automatic source diagnosis. |
| Operation properties | Typed observations and existing exact checking are usable; S.1–S.3 qualified four supplied scalar witnesses. | Eight operation/existence baseline cases, query correction, Nat/Int and infimum adapters and public stage remain open. Scalar checking is not automatic property attribution. |
| Real mathematical finding | The [PLD audit](../ladon-pld-core-source-audit/tasks.md) upheld an incorrect source reconstruction formula with an independently reviewed smooth witness. | This was a source-review discovery; full probability-law/Lean correspondence and general automatic detection are unestablished. The [sibling repair](../../../../lean/matrix-factorization/openspec/changes/fix-prv-density-reconstruction-sign/tasks.md) is complete within its bounded impact scope. |
| Matched reader-value pilot | The [completed r01 pilot](../ladon-matched-source-audit-pilot/evidence/run-20261113-r01/REPORT.md) has two frozen arm reports and two blind reviews: both arms judged faithful on all six selected claims, with zero upheld discrepancies or serious false accusations. | Primary gate not met. All selected claims were controls; source crosswalks were supplied in the original notes, and the Ladon arm used text analysis only. Native semantic evidence and sensitivity to a real fault were not tested. |
| Synthetic challenge r01 | Five paired units and ten audit reports completed; reported upheld faults: control two, assisted one. | Additional-finding gate not met. The accepted N.3a correction records the missed fault as false reassurance, with zero serious false accusations under the frozen definition. N.3 qualifies exposed application checks; prevention of silent premise import in fresh source reading remains unmeasured. One constructed source cluster, not natural-error discovery. |
| Fresh application diagnostic r01 | [Two constructed Mathlib units, four fresh audit arms](evidence/fresh-application-pilot-r01/REPORT.md): both arms correctly rejected an unconditional infimum-membership claim and supported a nonempty upper-ray claim. Assisted native completion on the valid unit passed replay and trust. | No added finding or measured effort benefit. This tests a small checked-application mechanism, not natural-source discovery or the broader historical gates. |
| Rational calibration source audit | [Bounded real exposition audit](evidence/rational-calibration-source-audit-r01/REPORT.md) mapped certificate soundness, eventual acceptance, adaptive transcript privacy, public seed, and randomized postprocessing to compiling Lean declarations. No fault was established in the selected passage. | Source and several owners are untracked in the sibling checkout; exact bytes are retained. The formal executable checker fixes a canonical range-reduction power; an arbitrary-power end-to-end wrapper and general source interpretation remain unverified. This is informed author review, not a comparative detection result. |
| Finite bracket calibration source audit | [Tracked real-source corollary audit](evidence/finite-bracket-calibration-audit-r01/REPORT.md) checked lower/upper terminal formulas, both profile directions, zero-noise monotonicity, feasible-set nonemptiness, and the infimum conclusion against a compiling Lean owner. No fault was established in the selected passage. | The source-to-formal object map was made by the informed root auditor. This is a bounded support result with no measured native Ladon contribution or unknown-fault discovery claim. |
| Hidden fixed-size f-DP subsampling map | [Informed source-to-formal audit](evidence/fdp-subsampling-map-r01/REPORT.md) froze the source's arbitrary-mechanism, hidden uniform exact-cardinality claim before inspecting Lean. Compiled types and fresh Ladon lineage establish an operator comparison; related exact-pair and Gaussian fixed-cardinality constructions were inspected. | The inspected results do not complete the source mechanism-to-output-law and trade-off bridge. This is unresolved formal support, not a mathematical refutation or an absence proof for the whole corpus. Ladon aided navigation and dependency authority; incremental detection benefit was not measured. |
| Gaussian mechanism candidate control | [Candidate review](evidence/gaussian-mechanism-map-r01/REPORT.md) compared the source GDP theorem with `GaussianDP`, event-level `ApproxDP`, and a concrete Gaussian-pair event bound. | Not eligible yet as a full positive control: the inspected owners do not bind the arbitrary statistic, neighboring output laws, sensitivity, and GDP conclusion in one theorem. This candidate screen was not independently reviewed or compiled. |

There is useful checked evidence and one real source finding, but no demonstrated incremental detection benefit from Ladon over the same LLM using ordinary Lean and the same mathematical recipe. The historical baseline and all three runtime children remain deferred. Task counts mix completed investigations with conditional engineering work and are not a percentage of product capability.

## Completed bounded milestone — explicit premise accounting

N.3 is complete as a bounded exposed development package: [report and consolidation decision](evidence/checked-application-n3c-r01/REPORT.md). Existing checks plus ordinary Lean suffice for the seven expected outcomes; the later bounded printer repair now gives C05 native completion with replay and trust acceptance. Consolidated guidance is delivered. The subsequent [fresh diagnostic](evidence/fresh-application-pilot-r01/REPORT.md) found no incremental detection benefit. The historical backlog is not the automatic next queue.

The [current decision and development contract](design.md#decision-after-synthetic-comparison-r01) govern N.3. The synthetic comparison is complete: assisted found one fault and control two; no added detection benefit was demonstrated. Its original aggregate misclassifies the assisted missed fault as a serious false accusation. The r02 review tightens N.3 around one checked application and conclusion transfer, explained by the premise ledger. The planning correction is recorded in design.md; the [accepted author correction](evidence/synthetic-launch-r01/SCORING-CORRECTION-v1.md) closes N.3a with the user’s separate-review waiver. Preserve the historical evidence. No new audit campaign or production diagnostic follows automatically.

- [x] N.3a Reconcile the completed comparison before drawing further conclusions. Read the frozen registration, per-unit first interpretations, final reports, checker receipts and adjudications. Complete the append-only/versioned [author reconciliation](evidence/synthetic-launch-r01/SCORING-CORRECTION-v1.md), identifying the old report/result hashes and each changed classification: distinguish a missed fault/false reassurance from a false accusation; evaluate qualified readings under the registered ambiguity rule. Record tool uptake and failed replay separately from successful ordinary Lean checks, and disclose treatment cues in reviewer inputs rather than claiming full blinding. Retain the unchanged additional-finding gate and unavailable cost telemetry. Separate independent review was explicitly waived by the user after current-session review and the unit-05 wording fix; retain original reports, scores, receipts and frozen policy. The author reconciliation finds one assisted false negative, zero serious false accusations under the registered definition, conditional support with unresolved scope on unit 05, and a still-failed additional-finding gate. Completed on the accepted author reconciliation and explicit user waiver; no independent-review claim is made.
- [x] N.3b Freeze the checked-application recipe and exposed qualification set. First interpret the passage and source definitions without presenting the candidate theorem; freeze objects, assumptions, quantifiers, conclusion and uncertain readings. Then expose the owner, record all revisions and bind one consistent instantiated application to the original source context. Make the premise ledger explain its arguments/residuals and require an explicit conclusion-transfer obligation. Freeze finite bounds and mathematically reviewed expectations for omission, faithful, conditional repair, derivable premise, shifted-state alternative route, shared-parameter mismatch and random-versus-common-limit cases. Use the design's symbolic countermodels and meaningful/harmless edits as bounded development checks; preserve library-specific meanings. Deliver executable steps and a small case manifest. A missing-operation proposal must identify failed existing functionality and exact evidence needed; no schema expansion is implicit. Completed: [frozen recipe, seven case expectations and ledger](evidence/checked-application-n3-r01/REPORT.md); Lean qualification remains N.3u/c.
- [x] N.3u Qualify one usable checking path in the environment actually delivered. Reuse the local capsule, pinned toolchain and 12 GiB bounds. Keep pristine manifest-controlled replay input distinct from the mutable project with packages/build outputs. Provide an exact working invocation for a source-context goal and proposed application, an expected unresolved case and a completed case with conclusion transfer; avoid manually transcribing a long theorem type or checking a theorem only against its own retrieved type. A fresh agent/user must obtain the intended semantic evidence using these instructions and actual delivered paths. Record setup, invocation failures and time to substantive evidence; diagnose any missing operation before proposing code. Capsule replay is needed only if this path relies on it. N.3a and mathematical control preparation may proceed independently of this qualification. Completed: [actual delivered source-goal path](evidence/checked-application-n3u-r01/REPORT.md), with root/fresh-user completed faithful checks and an explicit omitted-state residual. The tactic-hole probe was trust-rejected and retained; no counterexample or seven-case acceptance follows from this path qualification.

- [x] N.3c Execute and review the checked-application qualification after N.3b and N.3u (separate independent review waived by the user). For each claim retain the source interpretation, consistent object/parameter mapping, exact source goal, application/residual observations and checked conclusion transfer or explicit unresolved obligations. Reject completion claims supported only by a table, incompatible separately checked rows, added premises, or an intermediate application. Require justified support on faithful/derived/conditional and alternative-route controls as well as exposure of omissions and conclusion mismatches. Check counterexamples separately under every original premise and realize scalar models in the source setting. Report false reassurance, false accusations, justified support and unresolved readings separately. Record time to the first valid substantive query and correctly interpreted result, failures and unavailable effort. Record the user’s separate-review waiver without claiming independent evidence; consolidate verified guide and bundled/shared-skill guidance if existing tools suffice, or propose the exact missing operation. End with an explicit consolidation/implementation/pause recommendation and disposition proposed for the historical investment plan. No fresh comparative campaign follows automatically. Completed: [seven-case report](evidence/checked-application-n3c-r01/REPORT.md); C05 had ordinary Lean support and a native closure failure at the N.3 checkpoint; the later printer repair accepted native completion, replay and trust. The original failure remains retained.

## External strategic review r02 — reconciled after qualification

Received 2026-11-13 as the user-supplied response to `temp/ladon-semantic-strategy-review-data-r02.zip` (SHA-256 `35448afbc0985e566558d519353633c684e07af4906d750c116583045732efd2`). Reviewer identity is unspecified; the quoted 92% confidence is the reviewer's self-assessment. The packet is a source snapshot with no independent Lean replay. Initial intake recorded all claims as received / pending validation before source verification. The dispositions below now govern the bounded planning update; no experiment or implementation is accepted by this reconciliation.

Main recommendations: finish a tighter N.3 centered on one checked application under the original interpreted source context, with a consistent object map and checked conclusion transfer; make the premise ledger its explanation. Correct unit-03 false-negative scoring, preserve unit-05 conditional credit, disclose reviewer treatment cues and incomplete cost accounting. Qualify one usable checking path in the actual delivered environment, separating pristine capsules from mutable working projects. Proposed controls include source-only interpretation, shared-instantiation mismatch, two-point random versus deterministic limits, shifted-state lower bounds, symbolic countermodels and sensitivity to meaningful/harmless edits. Prefer consolidation unless a concrete missing operation is demonstrated. The recommendation to supersede the broad historical investment plan is a proposed scope decision, not automatic cancellation of its requirements.

Affected tasks: N.3a–N.3c, including N.3u, are now complete within their declared exposed-development scope. Historical umbrella 1–4 and linked child acceptance remain deferred. The current review dispositions below point to the correction and qualification evidence; the original r02 packet and experiment records remain historical snapshots.

### Review dispositions

| Review item | Disposition / evidence |
| --- | --- |
| Unit-03 category | N.3a completed the separately versioned author correction: missed fault with false reassurance, not a serious false accusation. Separate independent review was explicitly waived; none is claimed. |
| Unit-05 conditional credit | Both reports explicitly qualify support by the almost-sure reading; the registration scores conditional analysis on its actual reading. The accepted N.3a correction retains that supported reading alongside unresolved source intent and evaluates overstatement separately. It must not simply replace the case with a third faithful control. |
| Treatment disclosure | Confirmed in supplied reviewer cost inputs; independent review does not imply treatment blindness. No causal claim about the effect on ratings. |
| Command totals | Recomputed from all `command-*.result.json`: control 9 commands / 2 help calls / 57.516 seconds; assisted 45 / 21 / 99.404. These are summed command execution times, not total work or causal overhead. |
| Capsule and query usability | Source-confirmed exact-inventory validator and recorded failures; unit-05 reports a declaration-as-goal mistake and failed manual type transcription. N.3u qualified the delivered source-goal route with completed faithful support and an explicit omitted-premise residual, including fresh-user reproduction. It did not repair or rerun the earlier capsule failure. No weakening of capsule validation. |
| Checked application, object map and conclusion transfer | Adopted as a refinement of the existing N.3 correctness contract. Existing application observations are useful, but intermediate acceptance or a complete ledger does not certify final source-goal completion. |
| Source-only interpretation, model shapes, shifted-state and quantifier controls | N.3c checks the frozen seven cases, including full singleton/two-point models and the shifted-state ordinary Lean proof. Native shifted-state completion was rejected at N.3; the later printer repair accepts the retained corrected term. Source-only interpretation behavior, measurable-random-variable transfer, omitted-B-sign/pulse variants and comparative usefulness were not qualified; the seven cases do not cover every reviewer suggestion. |
| Real `Summable` semantics | N3Summable.lean and the retained real-summable-1 receipt qualify real Summable/norm equivalence on pinned local Mathlib. This is local checking, not independent verification of the external citation. |
| Supersede broad historical investment plan | Recorded as a recommendation requiring an explicit scope decision. Existing historical acceptance requirements remain deferred, not inevitable next work, completed or retroactively passed. N.3 ends with a consolidation decision and can recommend retirement. |

The initial r02 intake inspected source/report/registration/validator records and recomputed command aggregates only. Subsequent N.3a/u/c supplied the correction and checking evidence linked above. Neither stage establishes the cause of unit-03's reasoning error.

## Review checkpoint and conditional technical follow-up

Current-session source review checked the final singleton, two-point and shifted-state proofs against the frozen cases, inspected native outcomes and ordinary compiler/axiom receipts, and verified all 221 N.3u/c manifest hashes, the N.3b input freeze and retained final-source copies. It found no new mathematical defect in that scope. This review did not rerun Lean or provide independent review. Existing results remain exposed qualification with source interpretation attributed, not a fresh detection score.

The C05 limitation is resolved. The [diagnosis](evidence/c05-roundtrip-diagnosis-r01/REPORT.md) found that the inherited 5000-step printer emitted 22 omission tokens, leaving ten expression metavariables. The [production repair](evidence/c05-printer-fix-r01/REPORT.md) adds a finite explicit printer budget and rejects omission syntax before elaboration. The corrected whole proof now passes native completion, compiler replay and permitted-axiom checking. Preserve the earlier failures as historical evidence; neither another diagnosis nor another identical rerun is pending. U.1 subsequently resolved the distinct Adam heartbeat and generated-auxiliary replay failures. U.2–U.4 subsequently completed the field record above. U.5 subsequently completed the bounded primitive-to-two-family support question; unrelated reruns and runtime implementation remain unscheduled.

The source-only reading procedure was exercised in the [fresh application diagnostic](evidence/fresh-application-pilot-r01/REPORT.md): all four first interpretations preceded theorem inspection by auditor report, and both arms reached the correct final verdicts on a constructed omission and control. Its effect on false reassurance remains unestablished because neither arm made that error. The [rational calibration audit](evidence/rational-calibration-source-audit-r01/REPORT.md) and [finite bracket audit](evidence/finite-bracket-calibration-audit-r01/REPORT.md) checked real multi-declaration claims with ordinary Lean; neither established a new fault or Ladon-specific benefit. The subsequent [fixed-size f-DP subsampling map](evidence/fdp-subsampling-map-r01/REPORT.md) supplies a more informative negative support control: a matching public `C_p` operator and checked dependency closure do not themselves establish the source's hidden arbitrary-mechanism theorem. It is an informed unresolved mapping, not a new fault. The proposed Gaussian mechanism positive control was screened in [a follow-up map](evidence/gaussian-mechanism-map-r01/REPORT.md) and is also unresolved at the mechanism-to-GDP bridge, so it cannot yet serve as the faithful arm of that comparison. Select a narrower theorem with an actual complete law-to-privacy statement before registering a paired exercise. A new runtime operation requires evidence of a repeatable missing action. Any comparison needs independently selected inputs and separate registration. No further run is scheduled here.

## Completed challenge preparation and comparison

N.1 and N.2a–N.2c are complete. The [natural-source inventory](evidence/challenge-selection-r01/REPORT.md) retains its eligibility gap. The separately authorized synthetic track delivered [local capsule replay](evidence/synthetic-challenge-r01/REPORT.md), [workflow qualification](evidence/synthetic-workflow-r01/REPORT.md), [five validated cases](evidence/synthetic-evaluation-r01/REPORT.md), and [policy-v2 registration](evidence/synthetic-comparison-r01/REGISTRATION.md). All ten audit arms and subsequent adjudications have finished. [Readiness](evidence/synthetic-launch-r01/READINESS.json) and launch handoffs are historical preparation snapshots, not current invitations to launch. The [original result](evidence/synthetic-launch-r01/RESULT.json) remains preserved subject to the scoring correction above.

- [x] N.1 Specify and qualify one useful existing Ladon evidence route. The selected reader question is whether the PLD reconstruction formula for the law of `X` follows from the displayed `Y`-density, scaling, and sign conventions. The local derivation witness operation checks a supplied rational abstraction and assignment against exact premises/conclusion; expected evidence is a counterexample only when every encoded premise holds and the encoded conclusion fails. The previously frozen [r01 report and run receipts](evidence/source-consistency-r01/REPORT.md) qualify four outcomes (fault witness, repaired and unit controls, and assignment outside assumptions), and the [audit guide](../../../docs/PROOF_CORRESPONDENCE_AUDIT.md) records the executable recipe. Its source-side steps are: substitute the claimed density into the defining transformation identity; retain the source domain/regularity conditions; show the Gaussian witness is realizable in the original probability setting; and map the paper's `X,Y` and sign convention explicitly to the formal loss-law objects. The existing report confirms the scalar command does not prove those source conditions or the probability-law correspondence; the independently reviewed smooth Gaussian witness supplies source realizability. This route is useful for checking an explicit witness and exposing the consequence of a proposed reconstruction, but adds no demonstrated checking strength over a direct ordinary Lean proof of the same rational proposition. No missing operation is identified. Consolidate the existing guide/command as a bounded witness-checking workflow; do not claim that it discovers source formulas or improves reader outcomes. No rerun was needed because the frozen command outputs, expected values and independent review directly cover this operation. The DP-SGD route remains evidence of actual premise use, not a needed dependency for this formula question.
- [x] N.2 Prepare a separate challenge comparison only when source eligibility and workflow qualification justify it. Preserve completed N.2a and follow N.2p → N.2b → N.2m → N.2c; the deliverable is a ready registration/handoff or an explicit eligibility gap. A recorded gap completes the relevant investigation but leaves comparison readiness unmet. No broader paper rerun or feature integration follows automatically.

  - [x] N.2a Historical natural-source selection. Inventory candidate source/Lean units and establish answer custody. Start with the owner-nominated matrix-factorization notes and their formal counterparts; record exact revisions, bounded passages, a consequential reader question, candidate proof owners, known compilation evidence and prior exposure. Record exclusions and their reasons. A separate custodian/reviewer must establish at least one natural discrepancy, faithful material and a genuine ambiguity/abstention case before comparison readiness; an unresolved proof or absent formal owner is not a confirmed fault. Keep diagnoses, roles, fault locations, selected obligations and counterexamples out of auditor inputs. Deliver a candidate inventory, exposure/custody plan and readiness decision. If no eligible set exists, document the precise gap and the best candidates for further source investigation; do not create a mutation merely to meet the natural-fault requirement. Completed as a bounded inventory/gap result: [seven candidates and independent source-screen receipt](evidence/challenge-selection-r01/REPORT.md). At that inventory checkpoint, the screen established no natural discrepancy and no complete natural-source challenge was ready; the later synthetic capsule/comparison is separate.
  - [x] N.2p Extract the selected original proof into a local capsule and retain its compiled evidence. Start with C01 historical conditional descent and the smallest owner(s) covering the selected passage; C03 is a reserve if C01 cannot be bounded. Use this Ladon checkout and inspect current CLI help before planning. Treat matrix-factorization as a read-only donor: bind exact source/toolchain/import identities and source prose, materialize outside it under a new `temp/pitfalls-synthetic-r01/` directory in Ladon, and retain compact plans/manifests/receipts under `evidence/synthetic-challenge-r01/`. Preserve the original Lean statement, proof and trust policy. Use finite declared time/output/traversal budgets and the 12 GiB cap; record failures without automatic escalation. Replay in a fresh local work directory with no dependency on the sibling checkout; record pinned external package acquisition/cache provenance and unresolved external frontiers. Retain the capsule's native semantic dependency records; query/export further lineage only where the selected reader question requires it, using the capsule's own environment/index. Do not substitute lexical import/name edges for compiled lineage or require duplicate extraction of an already sufficient semantic graph. Verify hashes, exact target/type/value/trust agreement, absence of donor-path dependency and access to the necessary proof context. Deliver local capsule/replay evidence or the exact blocking boundary; do not claim a source snapshot or materialization alone is replay success. Completed: [local archive, native closure and verified fresh directory replay](evidence/synthetic-challenge-r01/REPORT.md); all five project modules rebuilt, exact native comparisons matched, peak sampled RSS about 6.05 GiB. The archive payload matches the replayed directory; its container identity is distinct. Offline dependency failure is retained separately.
  - [x] N.2b Qualify the smallest existing evidence route on the local original and separate exposed development material. Create any development mutations only in experiment copies, label them unscored and independently validate their mathematical meaning. The reader question determines whether context, premise routing or operation-property evidence is useful; do not force premise provenance onto every case. Record the executable recipe, local command/runtime/toolchain identities, finite bounds, expected evidence, reader consequence and unresolved authority. Preserve original-proof observation separately from checked provider terms and independent replay. Reuse sufficient capsule semantic evidence. Freeze and hash the generic workflow before evaluation mutations or their answers are disclosed to its developer or audit arms. Deliver qualification and a specific hypothesis about additional findings or reduced effort. Any missing-operation proposal must identify the exact mathematical obligation and failed interface before resuming an owning child; broad graph/API work remains deferred. Completed: [frozen workflow and independently reviewed development qualification](evidence/synthetic-workflow-r01/REPORT.md). Three supplied certificates accepted, one mismatched application rejected; scalar checking and reviewed stochastic realization remain distinct. No discovery or comparative advantage is established.
  - [x] N.2m Construct and independently validate a small synthetic evaluation set over the unchanged original Lean development. Start with one source cluster: a faithful original passage, two semantically distinct prose mutations, a harmless paraphrase, and a genuinely underspecified passage. This is a target composition, not preaccepted labels: reject or revise unvalidated candidates before registration and record rejected versions. Separate mutation authorship from mathematical review and from both audit arms. For each fault establish a precise interpretation and a counterexample or concrete missing source obligation under the passage's actual context; failure to prove a stronger statement is not a fault certificate. Check faithful controls and explain the multiple defensible readings that warrant abstention. Preserve the fully closed judgment and original assumptions in any formal refutation. Store exact mutation diffs, origins, labels, witnesses and reviews in custodian-only records; keep oracle Lean modules outside the audit import closure. Use mutations distinct from N.2b's development examples and do not tune the frozen workflow to evaluation answers. Deliver a frozen validated set or explicit unresolved labels, with one-variant-per-context input projection to prevent comparison with sibling variants from revealing the edit. Completed: [frozen v3 set and independent review](evidence/synthetic-evaluation-r01/REPORT.md), with two supported faults, two controls and one genuine ambiguity. Construction-stage evidence is source-mathematics validation only, with no new Lean oracle certificates; audit-arm execution occurred later under the separate registration. Prior drafts and the reviewed context correction are retained privately; original Lean and the frozen workflow are unchanged.
  - [x] N.2c If N.2p, N.2b and N.2m establish readiness, prepare a separate synthetic-challenge registration and fresh-context handoff. State that this measures controlled exposition-fault detection, not natural-error discovery or general reliability. Freeze input identities, source-cluster structure, exclusions, discovery versus supplied-obligation scope, optional access versus exercised workflow, and source-to-Lean crosswalk policy. Both arms receive equivalent local source/Lean inputs, the same complete mathematical recipe, model settings and comparable budgets/opportunities; require no live sibling checkout. Neutral case names, layout and metadata must not reveal labels; keep paired variants in separate fresh unit contexts. Give the control arm ordinary Lean and any shared preparation artifacts, and register Ladon's additional native evidence/tool access explicitly. Freeze the primary success criterion and any effort threshold before execution; preserve r01 and historical gates. Measure actual native tool use, underlying Lean attempts, extraction/replay failures and preparation/checking/review costs. Require preserved first interpretations/reports and independent adjudication. Deliver a reviewed registration or readiness failure; the separately declared comparison packet owns execution. Natural-source validation remains a later separately registered milestone. Completed: [registration](evidence/synthetic-comparison-r01/REGISTRATION.md), [handoff](evidence/synthetic-comparison-r01/HANDOFF.md), and [independent acceptance](evidence/synthetic-comparison-r01/REVIEW-v2.md). User-authorized policy v2 replaced lifetime child-process enforcement with twenty top-level checking commands. Runtime/setup qualification and the subsequently authorized ten-arm execution are complete; retain their actual session clocks and first reports.

### Existing route assessment and current eligibility

The [DP-SGD extraction report](evidence/dpsgd-roundtrip-r01/REPORT.md) and [M.1–M.3 adjudication](../ladon-premise-provenance/evidence/premise-comparison-m2-r01/ADJUDICATION.md) informed the completed challenge selection as a stronger candidate contribution than the bounded rational witness checker. N.3 delivered the checked-application workflow; U.2–U.4 delivered the subsequent internal-use exercise above. Ladon round-tripped one selected application and linked its mean and energy arguments to scoped locals supplied by Gaussian moment theorems; independent review upheld those structural links. Its demonstrated contribution is structured evidence of actual premise use with explicit provider and coverage frontiers. No cost or detection advantage has been established: the route was selected, source interpretation was supplied, costs were incomplete, and independent provider replay remains open.

[N.2a is complete with an eligibility gap](evidence/challenge-selection-r01/REPORT.md): seven candidates have exact source/owner snapshots and exposure records, and a separate custodian retained the detailed review of one bounded excerpt. That source-only screen reports zero supported natural discrepancies, three faithful units and one ambiguous unit; it does not certify the full paper or supply the missing fault. No complete eligible natural-source challenge emerged from that inventory; the later synthetic capsule and comparison are complete. Historical descent and the canonical high-noise Gaussian limit are the strongest bounded follow-up/control candidates at that selection checkpoint; the initialized-Adam route is a costlier reserve. The natural-fault requirement remains unmet for that completed investigation. The subsequent user decision permits synthetic preparation through N.2p/N.2b/N.2m without rewriting that result. The [original conditional-descent capsule is locally replayed](evidence/synthetic-challenge-r01/REPORT.md), the workflow is frozen, and [five synthetic cases are independently validated](evidence/synthetic-evaluation-r01/REPORT.md). The separately registered synthetic comparison is complete; its failed additional-finding gate remains unchanged, while [the original result](evidence/synthetic-launch-r01/RESULT.json) is interpreted through the accepted N.3a scoring correction. The natural-fault eligibility gap remains unchanged.

The PLD finding, authored scalar faults and DP-SGD route remain exposed development evidence. They can support workflow qualification or an explicitly labeled known-fault regression; they do not establish fresh discovery by this informed session. Fresh auditor contexts alone do not make a case held out from workflow development. Any later use of known material must disclose both auditor exposure and prior development use, with conclusions limited accordingly.

## Deferred production acceptance

Historical Tasks 1–4 below retain their original engineering and evaluation requirements. Accepted feasibility/provenance family baselines satisfy only those prerequisites; shared contracts and child acceptance are still missing. The operation child additionally needs baseline Task 1.3e and its eight-case baseline. The frozen feasibility baseline already detects both fixed faults, so the old requirement for an additional feasibility detection is unachievable on that population. Do not present finishing the remaining harness or scorer as a path to satisfying that unchanged improvement gate. A new evaluation objective requires its own registration; a completed new pilot cannot retroactively pass the old one.

## Completed correspondence/control preparation

This work is separate from historical acceptance tasks 1–4. The selected scope and source identity live in [design.md](design.md#selected-development-audit-dp-sgd-gdp-calibration). [The delivered report](evidence/dpsgd-gdp-r01/REPORT.md) owns findings, review and unresolved replay/coverage. D.1–D.4 record the work actually performed. They do not establish pitfall-detection capability, complete the real-source pitfall investigation, certify independent capsule replay or authorize a comparative pilot. The report’s closing suggestion to prioritize capsule replay or a general batch-comparison extension is superseded by the user’s correction below; the reviewed evidence itself is preserved.

- [x] D.1 Select the owner-nominated real source and identify candidate Lean owners; record prior exposure and a bounded reader question. Selection is complete; compilation and correspondence are not certified.
- [x] D.2 Freeze the claim inventory and first interpretations, exact parameter/assumption mappings, source and runtime identities, checking bounds and a faithful-control candidate before checking. Keep changed interpretations separately attributed.
- [x] D.3 Check the selected noise-to-utility chain using local-checkout Ladon and ordinary Lean. Preserve source-linked evidence and all unresolved obligations; add a capability only for a demonstrated missing operation.
- [x] D.4 Obtain independent review and deliver a complete bounded report, including reader consequences, unexamined material and effort. Decide afterward whether a separately registered fresh comparison is warranted.

## Completed bounded real-source pitfall investigation

Current result: the [selected descent-premise route](evidence/dpsgd-roundtrip-r01/REPORT.md) was successfully observed in an isolated local extractor after measured printing/heartbeat/output-budget adjustments. The actual argument/local identities show that the concrete Gaussian adapter supplies the generic estimate's mean and energy premises. This is a faithful control with no circularity fault established; whole-proof coverage and independent exported provider replay remain incomplete. Independent review upheld this selected route and its limits. P.1–P.3 deliver the bounded development probe; the diagnostic children and historical acceptance gates remain open. The successful experimental resource settings are not production defaults. The [scope correction](design.md#pitfall-objective-and-scope-correction) still governs the work; no mathematical fault is presumed. Historical attempts remain in the linked report.

- [x] P.1 Triage source-attributed obligations against assumption feasibility, premise provenance and operation properties. Select one mathematically consequential question and a faithful control; state what the C1–C4 checks do and do not already establish. Prefer a scoped premise route if it resolves a real reader question. Freeze the selected judgment, scope/assignment policy, expected evidence and unresolved boundaries before checking; do not require three separate studies merely to fill categories.
- [x] P.2 Exercise that selected pitfall obligation with existing local Ladon and ordinary Lean. For provenance, inspect actual proof use and the route supplying the premise; for feasibility, check independently closed dependency-preserving context inhabitance; for an operation property, preserve the original context and exact claimed property. Keep failures, positive controls and unresolved results distinct. If an operation is missing, document the concrete blocker before proposing a narrow implementation in its owning child.
- [x] P.3 Independently review the mathematical finding/control and assess what Ladon contributed. Deliver a source-linked pitfall report with explicit coverage and effort limitations. Update the relevant child with demonstrated capability or a concrete missing operation; preserve historical gates and do not infer detection improvement from a successful theorem/capsule check. Declare a fresh comparison separately if justified.

## Completed mathematical premise comparison and selected next audit

Current disposition is in the [reviewed adjudication](../ladon-premise-provenance/evidence/premise-comparison-m2-r01/ADJUDICATION.md). The practical procedure is consolidated into [the correspondence guide](../../../docs/PROOF_CORRESPONDENCE_AUDIT.md) and the shared [Ladon skill reference](../../../../codex-skills/ladon/references/proofir-and-correspondence.md). M.1–M.3 do not change historical baseline acceptance or close the broader umbrella gates.

The revised [PLD bounded audit](../ladon-pld-core-source-audit/evidence/pld-core-r03/REPORT-v2.md) is complete. Its [child task ledger](../ladon-pld-core-source-audit/tasks.md) owns current status and its adjudication owns the upheld source formula finding, independent all-ID review, mathematical control support and incomplete formal correspondence. No production extension or comparative benefit follows from this exposed development result.

The separately declared [matched pilot](../ladon-matched-source-audit-pilot/tasks.md) is now complete; current interpretation and next work are at the top of this ledger. Navier–Stokes remains a later isolated known-fault regression. Its answer and fault location are excluded from this plan.

The [post-acceptance consolidation note](../ladon-premise-provenance/evidence/premise-comparison-m2-r01/CONSOLIDATION.md) records guidance delivery and restoration of the accepted adjudication after a documentation edit caused a digest mismatch.

## Completed milestone: reusable source-consistency recipe

The source repair is owned by the completed [matrix-factorization packet](../../../../lean/matrix-factorization/openspec/changes/fix-prv-density-reconstruction-sign/tasks.md). S.1–S.3 are complete: [REPORT.md](evidence/source-consistency-r01/REPORT.md) records the updated guide/skills, four matching supplied-witness outcomes and independent review. The [registration](evidence/source-consistency-r01/REGISTRATION.md) bounds this exposed exercise. No new native detector, finalized investigation, source-probability proof or comparative gain was established. The subsequent matched pilot is complete; its negative gate and limited treatment coverage are recorded above.


- [x] S.1 Add the definition-substitution and exact object-map recipe to the audit guide, bundled skill and shared skill. Preserve original contexts, separate repairs and reject claim-ID drift. Verify links and skill validation; include the distinction between rational abstraction and actual source counterexample.
- [x] S.2 Freeze and run the four authored cases under [source-consistency-r01](evidence/source-consistency-r01/REGISTRATION.md) using the existing rational witness route. Verify expected outcomes, exact premise/conclusion values, faithful-control arguments and captured execution costs without changing historical baselines.
- [x] S.3 Independently review the recipe and retained results; deliver a report separating source finding, supplied-obligation checking, source fidelity and unmeasured discovery benefit. Record the next comparison requirements without launching a fresh experiment or broad integration.

## 1. Freeze the measurable contract

### External strategic review r01 — reconciled; development audit adopted

Source: external review supplied verbatim in the user message responding to `temp/ladon-semantic-strategy-review-data-r01.zip` (archive SHA-256 `c66d7fbffe4682a4158fe7aa08c264956351a97eac3a4a36129cf1fcad0a475a`, source snapshot HEAD `31df2116ee217e958edb9206afbd5f04e16697f0` plus packet-bound working files). Reviewer identity is not supplied. This records receipt; it does not authenticate the reviewer or independently replicate the reported runs.

The review recommends continuing with a smaller milestone: one complete source-linked audit using existing tools and recipes, adding only a demonstrated missing operation, followed conditionally by a separately declared fresh comparison. It proposes reducing the experimental shared contract and deferring the full scorer, remaining baseline campaign, broad adapters and integration. It identifies a saturated feasibility-improvement gate, possible declaration-kind cues in the corpus, the interpretation/value gap, fully closed negation and ambient-context risks, a `first`/partial-`simp` tactic concern, and a possible environment-export cause of auxiliary-proof replay failure. Initial intake labeled these claims received / pending validation. The dispositions below now distinguish documentary/source confirmation from untested runtime hypotheses and proposed scope changes.

Affected work at this historical review checkpoint: umbrella 1.2 and 3–4; baseline 1.3e, 1.4, 2–3; all three diagnostic children, particularly feasibility 1.1–1.2/2.1a and provenance route scope. The user adopted the smaller development audit. The later matched pilot separately froze and evaluated its own criterion; it does not alter the historical gates. The original review is the user-supplied message in this conversation; the packet remains the immutable source snapshot reviewed. No bundled code, new Lean experiment or external literature check was run for that reconciliation.


| Review item | Disposition and evidence |
| --- | --- |
| Saturated feasibility improvement gate | Confirmed from the accepted baseline and frozen specification: both fixed faults are already found. The old improvement objective is unachievable on this population; the full evaluation remains incomplete. |
| Earlier pilot had equal findings and greater cost | Confirmed against [the report](../ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/REPORT.md): 194.81 versus 285.09 summed seconds; 333,138 versus 419,530 accounted tokens; eight discrepancies localized in both arms, five controls accepted and one abstention. This is a report/source check, not a replay or a runtime-detector comparison. |
| Corpus has declaration-kind cues | Confirmed in `operation_semantics_01/02.lean` (`def`) versus `03/04.lean` (theorems). No exploitation is demonstrated. Preserve the corpus; expose this limitation in any discovery claim and avoid the cue in a separately designed study. |
| Fully closed judgments and let dependencies | Accepted correctness clarification. `closeChecked` universally closes ordinary locals; `_check_supplied_terms` negates the planned goal. An independent refutation must target the fully closed original proposition, or supply a premise-satisfying counterexample. The prototype already rejects ordinary ambient locals; this is not a finding that its accepted results are unsound. Operation design/spec and feasibility design clarify the boundary. |
| Query/type/toolchain correction | Confirmed existing Task 1.3e; needed only for its affected query path. |
| `first` plus partially successful `simp` | Pending pinned-runtime qualification. Do not infer affected baseline outcomes or substitute a new tactic in frozen records. A finishing-combinator alternative requires a separately versioned policy if adopted. |
| `_proof_1` export diagnosis | Initially an unconfirmed source inference. U.1 reproduced missing generated auxiliaries on the Adam consumer and repaired shared completion export, with legitimate-auxiliary replay and generated-axiom rejection controls. This does not qualify the separate feasibility prototype; its Task 2.1a remains owned by that child. |
| Smaller audit, scoped routes, explicit property recipes, deferred broad integration/scorer | Smaller development audit adopted after the user authorized continuation and selected the DP-SGD source. Broad runtime work stays deferred. See the selected scope in design.md. No historical task is completed or removed by this decision. |


- [ ] 1.1 Accept the [baseline child’s staged family baselines](../ladon-pitfall-baselines/tasks.md) against its [requirements](../ladon-pitfall-baselines/specs/ladon-pitfall-regression-evaluation/spec.md); record each child’s unlock separately, starting with feasibility. Verify the fixed corpus, original runtime, frozen common policy, isolation and independently reviewed immutable family reports before that child’s semantic edits. Keep this umbrella checkbox open until all three child unlocks are accepted; an accepted feasibility entry satisfies its baseline prerequisite; the common registration and shared evidence contract are also required before semantic edits.
- [ ] 1.2 Freeze the shared versioned envelope and each child payload contract, with explicit Python/native producer and reader ownership (including readers that must reject unsupported versions). Bind stage, judgment kind, exact subject, source/environment identities, parameter policy, execution bounds and evidence references. Verify negative schema/subject/authority tests, including rejection of an implication proof reused as an assumption-context witness and of fixed-assignment receipt reuse and document the opt-in addition in product scope without reopening unrelated frozen work.

## 2. Accept the bounded diagnostic children

- [ ] 2.1 Accept [feasibility](../ladon-assumption-feasibility/tasks.md) using its [specification](../ladon-assumption-feasibility/specs/ladon-assumption-feasibility/spec.md) and delivered acceptance report; verify independent context closure, leakage controls and all four family validation cases.
- [ ] 2.2 Accept [premise provenance](../ladon-premise-provenance/tasks.md) using its [specification](../ladon-premise-provenance/specs/ladon-premise-provenance/spec.md) and acceptance report; verify actual scoped routes, independently proved-provider controls and all four family validation cases.
- [ ] 2.3 Accept [operation definedness](../ladon-operation-definedness/tasks.md) using its [specification](../ladon-operation-definedness/specs/ladon-operation-definedness/spec.md) and acceptance report; verify original property preservation, actual typed operator identities and both existence and operation-family controls.

## 3. Deliver an integrated audit and readable report

- [ ] 3.1 Add the three opt-in stages to existing audit dispatch with shared deadlines and bounds; verify stage/resume, malformed-input, timeout, memory-stop and partial-frontier tests through the public CLI, and document an executable small example.
- [ ] 3.2 Project diagnostics into observation, inspection and report with separate fidelity/support/feasibility dimensions; verify contradictory-context, legitimate-conditional, repaired-claim and historical-receipt controls, including native reader rejection of unsupported versions.
- [ ] 3.3 Update README and relevant correspondence/contract guides plus bundled and shared Ladon skills to describe only verified behavior; run documented examples and skill validation, preserving unrelated shared-repo edits.

## 4. Qualify implementation and measured outcome

- [ ] 4.1 Run affected integration, strict quality and installed CLI checks on the final runtime; obtain independent code and mathematical-boundary review and resolve actionable findings with retained evidence.
- [ ] 4.2 Accept the [baseline child’s full 24-case baseline, validated scorer and matched evaluation](../ladon-pitfall-baselines/tasks.md) and independently reproduce case counts and per-family gates; preserve failures and unknowns without replacing cases.
- [ ] 4.3 Publish an acceptance report separating implementation readiness, measured development improvement and unmeasured discovery benefit; verify links to all child reports and leave a failed improvement objective explicitly unestablished. No paper rerun follows automatically.

