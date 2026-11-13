# Independent M.3 review — premise comparison r01

**Reviewer:** `/root/premise_m3_review`, gpt-6-luna, medium reasoning; independent of the M.2 report author.  
**Review completion:** 2026-11-12 19:52:19Z (observed). Independent start time was not recorded, so review duration is unavailable.  
**Checkout:** `/home/codex/projects/ladon`, HEAD `b4090c3a835aa1d21dc9546e191c0875cb2d5e15`; pre-existing dirty state was present, including OpenSpec edits and unrelated untracked files. No source or frozen packet was edited. No Lean run or extraction was performed.

## Integrity and evidence inspected

The frozen input manifest verifies in full: `premise-comparison-r01/SHA256SUMS` SHA-256 is `fb718488c2833c96b77a160f755a132fe04e4430b1c7ac6d42cfe9d6ee002067`; `sha256sum --check` reports every listed item OK. The actual first-report digest is `95ce4b93ec2171066b3e771839b24d02e95bd558d148e41d35bcd89ee58b4047`, matching `FINDINGS.sha256` (which records that same value). The input packet README, recipe, passages, CASES.json and actual frozen source/slice evidence were read. The M.2 `CORRECTIONS.md` addendum was also checked independently; its path/line corrections are upheld below. This review was exposed to the proposed labels and is adjudication, not blind discovery.

## Case judgments

### A — constructed omission: upheld, with an interpretation caveat

**Claim and scope.** CASES.json case A points to PASSAGES.md:7, whose full sentence sequence concludes “Thus P holds.” The stipulated complete-standalone scope expressly disallows supplying an unstated provider. Its attributed assertion is unconditional for arbitrary P.

**Formal route.** Frozen source `openspec/changes/ladon-pitfall-baselines/evidence/corpus/lean/CoreCases/premise_provenance_01.lean:3` gives the complete declaration telescope `(P : Prop) [h : PitfallCorpus.HasConclusion P]` and body `h.proof`. The class field is defined at `.../lean/Pitfalls.lean:9` as `proof : P`. In retained slice `.../premise-provenance-v3-family-20261112b/slot-4c19e2/proof-slice.json`, `nodes[0]` is the selected projection application; `arguments[1]` has `binderInfo=instImplicit`, type `PitfallCorpus.HasConclusion P`, and structural root fvar `_uniq 31298`. The matching `localContext` row (`name=h`, same localId) has that type and `letValue: null`. This proves actual use of an assumed provider in the original term, not merely presence in the telescope.

**Adjudication.** The first report is right to call this a supported *constructed* omission under the frozen scope. The sentence “A provider for P has a field...” introduces a generic description, not a supplied value or proof construction; “Applying this field projection establishes P” is elliptical about what is being applied. A reader could pragmatically repair it as “assuming such a provider,” but that conditional reading is not stated and conflicts with both the final unconditional conclusion and the packet's complete-scope rule. Preserve that caveat as a reader-interpretation limitation; it does not make the frozen case unresolved. This is an authored discrepancy and is not evidence of a real-source fault or autonomous prose detection.

### B — disclosed premise: upheld

PASSAGES.md:11 explicitly says “Assume that a provider for P has been supplied as a type-class instance” and concludes under that assumption. It is the same Lean source, declaration, and exact slice as A. Accordingly the observation itself cannot distinguish the cases; only the passage changes. The same argument/local identity establishes that `h` supplies the premise, and B discloses it directly. The implicit instance binder does not create an omitted-premise finding. This is a justified constructed conditional control.

### C — independently derived provider: upheld

PASSAGES.md:15 says to establish the arithmetic identity, package it, then project it. The retained slice `.../premise-provenance-v3-family-20261112b/slot-39d7a4/proof-slice.json`, `nodes[0].arguments[1]`, refers structurally to the constant `PitfallCases.PremiseProvenance04.provider`, rather than a local assumed instance. Frozen source `.../lean/CoreCases/premise_provenance_04.lean:3-5` defines `arithmeticFact : 2 + 2 = 4 := by decide`, constructs `provider := ⟨arithmeticFact⟩`, and projects it in `subject`. Together with `Pitfalls.lean:9`, this supplies the source route from provider field to an independently established proof. The historical successful compile/observe receipts and accepted baseline review are prior evidence; source inspection here is not a fresh replay of that provider. The justified-control judgment is supported, with that replay limitation explicit.

### D — selected mean/energy provider route: upheld, scope narrowed to the selected application

**Identity-bound retained slice.** Use CASES.json's repository-relative paths and ROUTE.json only for navigation. In retained `openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/dpsgd-roundtrip-r01/slice-attempt-05.json`, `source.path` is `Mf/Optimization/PoissonClippedSGD/GaussianStep.lean` and its source digest agrees with frozen source. `nodes[0]` is `expected_aligned_step_bound`, with 37 arguments. The authoritative same-scope data are `observation.applications[0].arguments[35,36]` and `observation.applications[0].localContext` (also reflected in the top-level selected node/context): argument 35 is the fvar `_uniq 36487`, matching local `hmean`; its let-value DAG root is the constant/application `gaussian_direction_mean`. Argument 36 is not a bare local: its root is `id` applied to the equality and the fvar `_uniq 36511`, matching `henergy`; that local's let-value root is `gaussian_direction_energy`. Thus the wrapper is preserved and the identities are root-reachable, not inferred from printed names. The values are observed original-term values; their theorem proofs have not been independently replayed from exported provider obligations.

**Source and conditionality.** Frozen `GaussianStep.lean` lines 58–59 derive `hmean` and `henergy`; the selected application begins at line 63, mean argument at line 66, and energy goal is discharged at line 68. `OneStep.lean` lines 110–114 show these are explicit hypotheses of the generic conditional lemma. The complete `gaussian_actual_one_step` telescope at `GaussianStep.lean` lines 17–38 remains in force. The manuscript passages named by CASES.json (source spans 58–84, 118–143, 685–705, 744–753 of the frozen TeX) state the update, theorem assumptions, exact sampling moments, and descent argument. The selected adapter route is therefore a faithful conditional/discharged-premise control for these two obligations, not an unconditional claim or a demonstrated fault.

**Limits.** The slice frontiers include `provider-boundary` and `provider-unreplayed` entries (including occurrences 35 and 36); they are retained limits, not evidence of failure. The slice has `complete: true` for its selected observation. The `coverage` statement (“selected application only; unselected providers and whole proof remain incomplete”) is in ROUTE.json, not a `coverage` key in the slice. This review establishes neither replay of exported providers, all theorem premises, whole-proof coverage, privacy calibration, feasibility, premise necessity, nor a whole-paper result. D was previously exposed and reviewed; this is a new review of the comparison route, not a blind experiment.

## Corrections to first-report navigation

The M.2 report's A directory used `premise_provenance-v3-family-20261112b`; the correct path is `premise-provenance-v3-family-20261112b`, as in the correction addendum. Its GaussianStep references 51–54 and 64–65 do not locate the cited derivations/application arguments: the verified locators are 58–59, 63, 66 and 68 respectively. These are navigation corrections, not outcome changes. The frozen first report and its hash remain unchanged.

## Disposition and limits of this milestone

Judgments: A upheld with a stated pragmatic-ellipsis caveat; B upheld; C upheld; D upheld for the two selected local premises only. No case is unresolved on the frozen scope. A's ambiguity is material to prose interpretation but the packet's explicit scope resolves the adjudication rule without rewriting the passage.

For these four exposed cases, the existing workflow suffices to identify the formal premise in use and compare its origin/disclosure against source, given retained slices and ordinary source inspection. No concrete missing operation is demonstrated. Ladon contributes identity-bound selected application arguments and local/value links (and D's visible retained frontiers); source reading supplies disclosure and justification. A separately declared value comparison is not justified by this evidence. Do not infer autonomous natural-language detection, necessity, general diagnostic accuracy, or lower effort. No matched user/workflow comparison was run, and no phase-specific preparation/checking/review effort or token measurements were collected for M.2; this review's wall-clock window is not an end-to-end cost comparison. No historical baseline score changes.


## Correction note

After delivery, the parent reviewer identified that the earlier metadata had borrowed the M.2 report start time. This revision removes that start and duration claim, keeps the observed report-completion timestamp, identifies the reviewer model/effort, and attributes the coverage wording to ROUTE.json rather than the slice. Case judgments are unchanged.
