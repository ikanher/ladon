# Mathematical reading qualification

Root-authored, exposed development controls, 2026-11-16. This is not independent
review, held-out fault discovery or a reader-benefit comparison.

## Result

The current native inspection preserves enough information to distinguish a
supported route, a refuted representation route for a true source claim, and a
refuted conclusion transfer for a false uniform claim. No additional missing
representation was observed on these controls. Existing formula, object-map,
closed goals, polarity and check receipts suffice for this bounded reading.

| Case | Source and mapping | Checked evidence | Reader consequence |
| --- | --- | --- | --- |
| Faithful | Every `i : Fin 5` satisfies `i.val < 5`; formal `n` maps to `Fin.val i`. | All five generated links supported, including actual conditional proof, premise supply and conclusion transfer; native replay/trust accepted. | Completed formal support for the attributed interpretation. |
| Wrong map | The **identical** source interpretation; formal `n` maps to `i.val + 5`. | The actual formal conditional theorem still checks. Premise supply is refuted by `i = 0`, giving `5 < 5`. Other unchecked links remain open. | This map cannot supply the theorem's premise. The source claim is true, as separately compiled in `ContextFixture.original_source`; source falsity does not follow. |
| Uniform | A pointwise theorem `∀ n, ∃ k, n < k` is offered for a uniform bound `∃ k, ∀ n, n < k`, with an irrelevant universally quantified parameter retained for the selected application. | Actual conditional proof accepted; conclusion transfer refuted by choosing `n = k`. | This theorem does not support the attributed uniform reading. A **separate** ordinary Lean proof refutes the original attributed proposition. |

[RESULT.json](RESULT.json) records root verification. [read_results.py](read_results.py)
rechecks retained identities, original inputs, all nine native completion/replay/
trust results, complete inspection coverage, exact receipt targets and expected
outcomes. It does not perform a new Lean replay.

## How to read the evidence

1. Start with `context.interpretation.value.record` and `loweredFormula`, not the
   welltypedness obligation `P → P`. That obligation does not establish `P`.
2. Compare `objectMap` and `context.formalSlice` for the selected application.
   Faithful and wrong-map inspections have the same interpretation reference,
   different map terms and different plan identities. The source was not silently
   replaced to obtain a successful check.
3. Locate the exact `premise-supply` or `conclusion-transfer` goal in `obligations`.
   The generated goal retains the map as a let binding, plus original source
   assumptions, selected formal premises and quantifier order.
4. Resolve its `checkEvidence` receipt. In both fault routes, mode is `refute`
   and `checkedGoal` is the negation of that **link**, not automatically the
   negation of the original interpreted formula. Matched stored bindings describe
   receipt consistency; mathematical authority comes from the retained actual
   completion/replay/trust records.
5. Keep the original source question separate. The wrong-map source has its own
   proof. The uniform reading has its own refutation. A failed selected route
   can coexist with a true source and an alternative valid route.

The `representation-transport` goal in this profile elaborates the declared map's
type with a final target `True`; it does not certify the map's intended meaning.
The substantive mathematical checks are the mapped premises and conclusion.
This qualification does not require a separate dependency graph: those
relationships remain present in the actual closed targets.

## Inputs, execution and limits

[FIRST-INTERPRETATION.json](FIRST-INTERPRETATION.json) precedes extraction/checking
and discloses root exposure to existing controls. The first Fin interpretation is
byte-identical between the two maps. [INPUTS.json](INPUTS.json) binds the three
primary local project inputs and relevant Ladon implementation files. The donor
matrix-factorization checkout was not used or changed.

The local [project](project) uses only Lean, pinned by `lean-toolchain`. Its
`original_source`, selected formal conditional and pointwise theorem compile
without axioms; see [source-control.process.json](source-control.process.json).
[SourceRefutation.lean](SourceRefutation.lean) independently refutes the exact
attributed uniform proposition without axioms; its receipt retains the harmless
unused-parameter warning. The source-to-formula mapping remains attributed.

[run.py](run.py) invokes public extraction, interpret, align, check and inspect
commands through this checkout's entrypoint. Its main sequence completed in
272.81 seconds, within a 900-second whole-sequence bound and 300-second per-command,
12-GiB process-tree and 8-MiB captured-output limits. A later separate source
refutation used a 60-second bound and the same memory/output caps. Process receipts
are retained for every command. Inspections used an explicit 8-MiB context
allowance. No resource stop or failed mathematical check was hidden; no native
source-goal completion was credited for the separate ordinary Lean proofs.

Full alignment/check/inspection bundles are retained under [faithful](faithful),
[wrong-map](wrong-map) and [uniform](uniform). They include pinned environment and
executable identities, generated targets, supplied terms, process accounting and
replay/trust evidence. No portable transitive compiled dependency closure or
independent replayer exercise is claimed. MANIFEST.json binds retained evidence,
excluding disposable `.ladon` state and Python caches.

## Disposition

Consolidate the existing reading recipe. No new ProofIR payload, automatic graph
inference or production diagnostic is justified by these three cases. A new
representation should name a mathematical relationship that the current formula,
map, closed goals and receipts cannot preserve or expose. Fresh reader usefulness
and more complex stochastic/mechanism contexts remain unmeasured. Historical
pitfall acceptance and comparison gates remain unchanged.
