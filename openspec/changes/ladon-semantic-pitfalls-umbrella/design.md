# Design

## Context

See proposal.md and [the inspection record](inspection.md). Current correspondence generates H → P and H → C → N, while source-goal completion independently replays proofs with the standard axiom policy. Selected provider extraction and typed operator observation already exist. Feasibility, source justification and intended operation properties are not implied by those guarantees.

The main spec inventory contains probe, identity and orthogonal authority contracts; this umbrella adds a consumer without modifying them. Unarchived contract and Real-prose changes retain separate acceptance and discovery gates.

## Goals / Non-Goals

**Goals:** make the three missing diagnostics usable through existing investigation commands; expose checkable evidence to an LLM without overstating source fidelity; measure incremental behavior on fixed cases.

**Non-goals:** universal prose translation, arbitrary consistency deciding, theory-of-computation or philosophical verification, proof of kernel/hardware correctness, another paper-specific auditor, full-paper retest, search optimization or caching. No source text is automatically rewritten.

## Decisions

### Ownership and order

| Packet | Owns | Depends on |
| --- | --- | --- |
| [Baseline](../ladon-pitfall-baselines/tasks.md) | corpus, baseline, scorer, matched measurements | none |
| [Feasibility](../ladon-assumption-feasibility/tasks.md) | exact context inhabitance/refutation evidence | accepted family baseline |
| [Provenance](../ladon-premise-provenance/tasks.md) | actual premise/field/instance paths | accepted family baseline |
| [Operations](../ladon-operation-definedness/tasks.md) | typed expectations and property obligations | accepted family baseline |
| This umbrella | stage dispatch, report/inspection, docs/skills, final acceptance | all three semantic children |

The [baseline child's corpus review and follow-up obligations](../ladon-pitfall-baselines/tasks.md) govern readiness: exact hashes and direct compilation alone do not establish original-subject fidelity, control coverage or oracle isolation. Preserve its requirement-to-evidence review before accepting the freeze.

The baseline child owns the staged unlock in its [family baseline requirement](../ladon-pitfall-baselines/specs/ladon-pitfall-regression-evaluation/spec.md). Its Task 1.4 records acceptance separately for each child; feasibility runs first. An accepted family baseline plus the shared evidence contract unlocks that child’s semantic runtime work without waiting for the full scorer or the remaining families. All baseline batches use the same preserved pre-change runtime and policy, even when run after another child has changed the working tree. The full 24-case baseline, scorer, matched enhanced run and unchanged improvement gates remain required for final umbrella acceptance.

Common registration freezes evaluation configuration; later family harness implementation and qualification accompany their batches under the [baseline design](../ladon-pitfall-baselines/design.md#registration-and-later-runner-qualification). Baseline measurement may retain independently evidenced unsupported diagnostics. Implementing a new semantic child is never a prerequisite for measuring its original-runtime baseline.

### Reuse the checking boundary

Extend existing contract-audit operation dispatch and investigation reporting rather than create a second proof checker. Child planners emit exact generated goals; existing capture/completion/replay supplies authority. ProofIR stores distinct context, provider and operation observations bound to their owners. Prefer existing registered evidence kinds; any necessary new closed payload/version must be reviewed before emitting it. Do not insert ad hoc fields into existing canonical v3 records.

Receipts distinguish observation, checked conditional fact, source-reviewed expectation and confirmed discrepancy. A child finding can be useful even when source fidelity remains unresolved. A report must show exact source and formal scope, expected property, supplied/absent evidence and next missing obligation. No global “safe theorem” badge. A proof of a supplied implication is formal support for that proposition; it cannot be mapped to an inhabitation certificate for its assumptions. In particular, r18 case 03 proves `False → True` while the premise `False` remains uninhabitable. Treat the legacy baseline label `witnessed` according to its proposition subject, not as a new context-feasibility receipt.

### Public workflow and bounds

Add opt-in stage names to the existing contract audit plan: assumption-feasibility, premise-provenance and operation-definedness. The umbrella owns the common versioned request/result envelope, dispatch and report consumption; children own their mathematical payloads and generated obligations. Task 1.2 must name the producer and Python/native reader for each boundary and freeze subject, judgment-kind, source/environment, parameter-policy, bounds and evidence-reference bindings before emission. Unsupported reader versions must fail explicitly. No shared schema is accepted by this planning clarification alone. Planning does not launch Lean implicitly. Explicit execution shares the audit deadline, inherits stricter stage bounds and preserves the 12 GiB process-tree cap. Source/fingerprint, output, traversal and stop diagnostics reuse existing supervisors.

Saved inspection is historical; fresh execution is separately requested. Existing correspondence support states remain unchanged, with new diagnostic dimensions explaining limitations. Check failures and resource stops never become proof of a pitfall.

### Product scope and acceptance

docs/PRODUCT_SCOPE.md contains an older broad runtime freeze. The user subsequently authorized application of this umbrella and completion of the baseline corpus task. That authorization covers the planned bounded work; unrelated expansion remains outside scope. Implementation should record this direction in that document at the existing product-scope task. The incomplete baseline is a work dependency, not a request for further user permission.

Engineering acceptance and the matched development improvement gate are separate. The child baseline defines the measurable gate; a failed gate completes measurement with a negative result, not the improvement objective. A future unfamiliar-source evaluation requires separate custody and authorization; this work does not close the old contract-evaluation gates.

## Risks / Trade-offs

- [False accusations from legitimate assumptions] → require source-role review and explicit conditional/contradiction controls.
- [A supplied proof mistaken for automatic discovery] → keep validation, bounded tactic search and source-reading tracks separate.
- [Expensive extraction] → measure before optimizing; preserve bounded frontiers and reuse already qualified extraction rather than broaden every case.
- [New records grow the consumer surface] → version only necessary boundaries and test legacy inspection/installed CLI before acceptance.

## Migration Plan

Opt-in additive stages and versioned evidence leave old receipts untouched. Update Python validators, stored inspection and any participating native reader together; unsupported readers must reject unknown versions explicitly. Rollback disables new dispatch without deleting evidence. Update README, relevant guides, bundled skills/ladon/SKILL.md and the shared ../codex-skills/ladon/SKILL.md after verified behavior exists. No publishing or push.



## External review r01: proposed next direction

The [review reconciliation](tasks.md#external-strategic-review-r01--reconciled-development-audit-adopted) recommends testing the practical value of one complete source-linked audit before integrating three diagnostic stages. The user subsequently authorized this smaller development audit and nominated the DP-SGD analytical Gaussian note. The existing specifications and historical gates remain in force; broad diagnostic implementation stays deferred. The older shared-contract-first sequence is not the reviewer’s recommended next milestone.

The proposed deliverable is one realistic, multi-claim source excerpt with its actual compiling Lean counterpart and a comparable faithful control, selected independently of diagnostic-example construction. Preserve the source inventory, first attributed interpretations, checked local obligations and unresolved coverage. A second reader should be able to identify what was proved, under which assumptions, and how that changes the reading of the passage. Reuse existing capture, completion/replay, provider/typed observations and ordinary Lean recipes. Add a narrow operation only when the exercise documents a concrete missing capability; scoped premise routing is a candidate, while proof-position feasibility depends on a demonstrated reconstruction need.

A minimal experimental record can carry source span, interpretation attribution, complete formal judgment, parameter policy, environment, method, evidence and unresolved scope without changing canonical production records. Broad child payload schemas, unused native readers, general provider graphs, special operation adapters and the full scorer are deferred during this development audit, not cancelled or completed. Baseline Task 1.3e is needed only if the selected exercise uses its query path. Any production change still needs its applicable correctness and compatibility checks; a pilot is not a way to bypass them.

Only after a useful development exercise, consider a separately declared small fresh comparison (the reviewer suggests roughly six to eight short units). Compare the same LLM, ordinary Lean and the same recipes with and without the thin Ladon workflow, using equivalent sources, budgets and opportunities. Exclude selected obligations, diagnoses and counterexamples from discovery inputs; any later supplied-obligation track is distinct. Include faithful and ambiguous passages, preserve first reports and independently adjudicate findings, false accusations and warranted abstentions. Account for preparation, human review, elapsed time, tokens and Lean attempts. Preserve the frozen 24-case population and its saturated improvement gate separately.

Continuation would require useful additional upheld findings without new serious false accusations, or a predeclared material reduction in total effort at matched quality. A single success warrants further investigation, not a general accuracy claim. Consolidate around existing commands/recipes if added machinery costs more without useful benefit; redirect toward interpretation if obligation selection dominates failures. The selected development source is recorded below. The primary comparison criterion and practical threshold must still be declared before a comparison starts. No run budget or numerical improvement threshold is inferred from the review. The next external review should inspect the real units, first interpretations, checked evidence, adjudications, comparative costs and the exact added operation.


## Selected development audit: DP-SGD GDP calibration

The user nominated `../lean/matrix-factorization/latex/natural-language/dpsgd_analytic_gaussian_bound.tex` and identified the scientific objective: convergence-rate and batch-size predictions using GDP calibration instead of the Abadi noise scaling. This is a real development target selected by the owner, not an invented diagnostic fixture or fresh held-out evaluation.

Reader question: **For the specified Poisson-sampled clipped SGD run, what finite expected-gradient bound and optimal learning rate follow from the selected GDP noise variance, and which privacy and batch-comparison claims require additional conditions?** An upheld limitation or justified support can help the reader; finding an error is not a prerequisite for completing the audit.

Selection snapshot (2026-11-12; not a replay receipt): sibling HEAD `73567feeab6e4fd2fa4931dbaf2731bbe7900e8e`; manuscript SHA-256 `7c2dadfe52bf7c735c1eaf47d109786325326d959c9538d44b2b7b4e20b0dc1d`; `lean-toolchain` SHA-256 `302cd63c54178885b89e669f33b38f12f4dd7ae7e5cac537b3203e3768d8fb2b` (Lean 4.33.0); `lake-manifest.json` SHA-256 `56c1b71846349db8473a42af6d1f5979e07e9f3f248eb9ae2510cfb59c94465d`. The sibling working tree contains unrelated work; HEAD alone does not identify all inputs. Freeze relevant Lean source bytes and the local Ladon runtime before checking, and reverify these selection identities.

### Initial bounded scope and candidate correspondence

Read the main statements and calibration discussion (lines 43–363), with the utility proof (685–773). The first complete checking unit is `thm:main`, `cor:rate` and their GDP substitution (`eq:clt-D`): actual sampling/noise law → finite expected-gradient bound → admissible bound-minimizing step. Treat the fixed-update part of `prop:clt-batch` as a follow-on local obligation; keep exact-pass comparisons and the q=1 endpoint visible in the inventory without assuming they are already covered. Do not silently turn the bounded exercise into a full 1,288-line paper audit.

All Lean paths below are relative to the sibling repository. These are source-inspected candidates, not accepted correspondences:

| Source claim | Candidate formal owner | Meaning to check |
| --- | --- | --- |
| `eq:noise`, `eq:clt-calibration`, `eq:clt-D` | `Mf/Optimization/PoissonClippedSGD/GDPFormula.lean`: `gdpFormulaNoise_sq`, `gdpFormulaNoise_energy`, `poissonRateD_eq_gdpFormulaD` | Multiplier variance versus coordinate noise versus total Euclidean second moment; positive domains; raw subsampled formula versus full-sampling formula. |
| `thm:main`, utility appendix | `Mf/Optimization/PoissonClippedSGD/Convergence.lean`: `gaussian_convergence` | Actual recursion and history law; measurability/integrability; expected pre-update gradient norm; exact initial gap versus public upper bound F. |
| GDP-specialized utility | `Mf/Optimization/PoissonClippedSGD/GDPUtility.lean`: `finite_sum_gdp_formula_convergence` | Finite-sum objective assumptions versus the manuscript's general objective with mean query gradient. |
| `cor:rate` | `Mf/Optimization/PoissonClippedSGD/GDPStepsize.lean`: `stepUpper_optimal`; `GDPApplications.lean`: `finite_sum_gdp_formula_convergence_tuned` | Optimizing the bound, admissible cap, F>0, same noise law, public tuning inputs and actual consumer. |
| Fixed-update part of `prop:clt-batch` | `Mf/Optimization/PoissonClippedSGD/GDPBudgetAnalysis.lean`: `gdpUpper_retuned_antitone_batch` | Same T and problem parameters; varying admissible caps; q=1 needs the separately defined exact Gaussian branch. |

The unconditional positive-variance utility theorem is a candidate faithful control for the GDP substitution. Its fidelity and comparable scope require review; do not label it a validated control merely because it compiles. Preserve the distinction between a convergence theorem at a chosen variance and a finite private-convergence theorem at that same variance. A comparison of upper bounds does not order realized training performance.

### Exposure, exclusions and completion boundary

The main source already explicitly separates finite utility from asymptotic privacy and discusses limitations of the inverse-CLT prescription. These are source facts, not newly detected faults. During selection we inspected adjacent result/audit metadata and candidate target mappings, and the sibling OpenSpec note `dpadam-batch-size-accounting-umbrella/dpsgd-certified-utility-transfer.md`. Therefore this exercise is informed development work. Existing diagnoses, theorem mappings and retained checks cannot serve as fresh discovery or fresh replay evidence. The adjacent result manifest has no canonical targets, links or reviews; this is a provenance limitation, not proof that the mathematics is false.

The separate finite privacy appendix, finite-error corrections, numerical accountant tables, fixed-pass asymptotics and finite counterexample appendices remain outside the initial checking unit. Inventory their relationship to the reader question and mark them unexamined. In particular, do not borrow a proof at the separate sufficient variance to certify the raw GDP variance. Source literature claims about Abadi/Bu remain attributed to the manuscript unless separately verified.

Use Ladon from this checkout, alongside ordinary Lean with the sibling pinned toolchain. Freeze first interpretations before obtaining new checker results; preserve all premises, lets and closed targets in positive and negative queries. Record preparation, checking and review effort and extraction/replay failures. Deliver source-linked support, discrepancies or explicit unresolved outcomes with independent review. No new production stage, whole-paper rerun, quantitative product-benefit claim or fresh comparison follows automatically.


## Pitfall objective and scope correction

After the first C1–C4 correspondence/control report, the user reminded us that the project is the semantic-pitfall investigation. Checking the convergence chain and materializing a capsule supplied useful formal support and a control candidate, but did not test the proposed diagnostic questions or identify a missing Ladon capability. Preserve that evidence and its independent review; do not count it as completion of the real-source pitfall milestone. The report's suggested next priorities (independent capsule replay or a general batch-comparison extension) are superseded as the main development frontier. Either may be supporting work if a selected pitfall question actually requires it.

Use this real source to triage three kinds of questions, then select one useful bounded obligation rather than launching all three implementations:

- **Assumption feasibility:** Can the context of a selected scientific application actually hold, with its fixed parameters and dependent definitions preserved? A successful conditional convergence theorem does not answer this. Conversely, an explicit conditional theorem is legitimate; a witness for one assignment is not uniform feasibility over all parameter choices. A trivial constant-objective witness alone may not answer the intended nontrivial application question.
- **Premise provenance:** Where does the proof obtain the local descent/variance or calibration premise needed for the claimed conclusion? The selected route must identify actual original-proof use and its supplying argument, and distinguish an explicit assumption from a derived fact. A declaration dependency graph or a newly constructed valid implication does not establish this route; a route does not establish necessity or circularity. Start by considering the descent premise consumed in the convergence proof and its source derivation, not by asserting it is faulty.
- **Operation properties:** What source-attributed property of a reciprocal/logarithm, square root or chosen optimizer is needed, and where are its positivity, domain and cap conditions supplied? Lean's total operations are not errors by themselves. Existing C1–C4 positivity/admissibility support is control evidence; repeating it cannot be called new fault detection. Check a consequential remaining property only if the source actually claims it.

The reader-benefit endpoint remains one complete source-linked audit: an upheld pitfall, a justified faithful case, or an explicitly unresolved question, together with what existing Ladon contributed and any concrete missing operation. Do not assume the selected note contains a fault or manufacture one. Authored mutations, if later useful, need separate identities and must not be reported as findings in the original source. The external review's recommendation to defer broad integration remains in force; restoring the pitfall objective does not authorize automatic implementation of all diagnostics.
