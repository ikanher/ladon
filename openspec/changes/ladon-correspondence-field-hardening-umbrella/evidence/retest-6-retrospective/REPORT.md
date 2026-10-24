# Retest-6: reference reconciliation

Operator/development material, 2026-10-18. **Contains the reference answer.**
Exclude this directory, its parent development evidence, and the reference from
future blind auditor inputs. No historical report, primary source, runtime,
acceptance test, or handoff was edited. No new blind run or Lean replay occurred.

## Decision

**Retest-6 recorded both discrepancies identified by the preserved reference.**
It did not establish a false mathematical assertion. Those are different outcomes.
The earlier recommendation to locate a wholly missed passage was premature.
The first visible loss is from human observations to structured findings and
the final outcome summary, with an upstream mismatch in the stated objective.
Prioritize that path before extraction scaling or another full-paper run.

The reference is Bastounis–Circelli–Hansen,
`NavierStokes_LostInTranslation_ArXiv.tex`, SHA-256
`67b27489185bf10baa92192a47ca25d51ecd4ed320b51374b5571a9cba13c084`.
It was preserved in Ladon's correspondence-discovery evidence after its original
Quux directory disappeared. Its introduction explicitly disclaims a judgment on
the correctness of the NL proof: the alleged defects are mistranslations into Lean.
Its two Navier–Stokes examples compare intermediate statements and methods.
It supplies no target counterexample to the prose.

The retest handoff instead starts with “The user reports an error in the
exposition.” Its subsequent instructions distinguish correspondence and method,
but its opening and the final headline invite a falsity-only interpretation of
success. The frozen report's negative mathematical claim remains accurate;
“the reported error was not identified” is too broad relative to this reference.
This is a new retrospective disposition, not a revision of that first report.

## Reference-to-run comparison

| Stage | Inverse estimate, (8.19) | Pressure flux, (10.19) |
|---|---|---|
| Reference allegation | Four extra torus derivatives in prose, five in selected Lean results; different summation power | B_R-only prose bound versus A_R-dependent formal bound; different Riesz/Hölder/Sobolev route |
| Located during audit | Yes: `fresh-phase-geometry/first-assessment.json`, limitations[1], frozen 19:57:05 UTC | Yes: `terminal-comparison-audit/first-assessment.md`, assessment and pressure-route paragraphs |
| Human interpretation | Explicitly records four versus five and a separate justification for the prose | Writes both envelopes and explains why the formal endpoint does not replay (10.19) |
| Structured claim/finding | Missing from the reviewed main inventory plan: `claims: []` | Missing from the same plan; selected native work instead pursued harmonic pressure recovery |
| Exact native bridge | Unlocated; no exhaustive absence claim | Not provided for the displayed pressure bound |
| Summary | Mentioned as weaker formal statement and unlocated counterpart, but headline says target unidentified | Mentioned as different valid pairings, but headline says target unidentified |
| Retrospective disposition | Reference discrepancy observed; mathematical falsity not established | Reference discrepancy observed; mathematical falsity not established |

The inverse reviewer inspected `inverse_finiteJets` and
`mixedJet_inverse_bound`. This retrospective additionally checks the reference's
nearest torus-only statement `norm_derivativeWord_inverse_le` at lines 1059–1080.
It requests pure coordinate derivatives of order `w.length + 5`, using
`coefficient_seminorm_bound` with a fourth-power summable weight. The prose uses
four additional derivatives and a third-power summable weight in dimension two.
Taking a finite maximum over derivative words is needed to obtain a norm statement;
mixed slow-variable jets must not be conflated with torus derivatives.
Smoothness alone supplies no uniform fifth-derivative bound from a fourth norm.
This confirms the selected guarantee difference, not falsity of the four-loss
estimate or absence of some other exact formal counterpart.

The pressure theorem `exists_uniform_actual_pressure_flux_bound`, lines 576–599,
contains `(sqrt(B_R)+1)*(A_R/R+1/R^2)` plus the commutator term. The prose has
`(B_R+1)*sqrt(B_R)/R` plus that term. The available inequality
`B_R <= C*(A_R + M/R)` cannot eliminate A_R from an upper bound: its direction
is wrong for that purpose. Scalar independence is only a failed-transfer witness,
not a counterexample realized by PDE solutions. The time quantifiers also differ
(a.e. versus all interior times); constants are uniform in R. Opposite signs of
both field differences cancel in the flux. Both routes can support the downstream
uniqueness argument without being the same intermediate proof.

The run gives ordinary mathematical arguments supporting the prose in both
places. This retrospective does not certify those complete analytic arguments;
it checks their bearing on the reference allegation. A separate proof never
erases an observed mismatch with the selected original formal route.

## What the runtime contributed, and what it missed

`plan-08-inventory-compact.json` has 111 units marked surveyed/done and zero
claims. The final main receipt likewise reports zero claims, zero actionable
items, and one blocked harmonic counterpart. The observed mismatches remained
in narrative reports. Thus this run is evidence of human localization and
comparison, not native discrepancy detection or measured Ladon benefit.

There is also a reproducible reporting omission after an authored mismatch is
recorded. `investigation._claim_queue` counts a reviewed `mismatch` or `different`
judgment as reviewed; v1 status returns counts but no finding projection.
`assess_structured` projects the base plan to v1. Its bundle summary retains
`methodReview`, but `_review_summary` uses classification to determine review
completion without exposing that classification in the summary row. Neither
completed review nor recorded formal links means a matching statement.
The narrow bookkeeping contract explicitly disclaims semantic completeness;
these are missing product capabilities, not a demonstrated kernel soundness bug.

The frozen lattice and model terminal receipts already preserve
`methodReview: different-attributed`. These are useful controls: successful local
support and method difference must coexist, without becoming false-paper alarms.
Model B.11 also retains the containing-theorem dependency qualification.

The 4096-node extraction failures, 32 MiB plan limit, and approximately 52 minutes
of observed correspondence-command activity are real costs. They do not explain
failure to *notice* these two discrepancies: the evidence says they were noticed.
Cost improvements and coverage scheduling remain secondary until a specific
consumer and benchmark justify them. The command union includes concurrent work;
it is not 52 minutes with no mathematical reasoning.

## Regression evidence and limits

`cases.json` pins two reference discrepancy cases and six successful local
controls from the frozen run. Four controls have the same method; model bounds
and lattice count have different valid methods. All six preserve local scope,
original obligation IDs, first reviews and native artifact identities. The new
manifest binds 31 original files; the verifier checks identities and their
recorded labels, not mathematical truth or fresh Lean replay.

`probe_runtime.py` exercises portable reviewed cases through the public CLI using
the current local checkout. `test_reporting_contract.py` is an **unimplemented
acceptance proposal**, outside the frozen test suite. It requires non-lossy
reporting of authored mismatch/method judgments and keeps an aligned control.
Failures demonstrate the reporting requirement, not autonomous discovery.

No causal score, fresh detection success, or revised blind success rate follows
from this answer-informed reconciliation. Qualitatively, both reference topics
were observed. Exact original-contract reproduction and independent review of
each complete bridge remain distinct stronger milestones.

Read [WORKPLAN.md](WORKPLAN.md) for the bounded next implementation and stopping
criteria. Existing umbrella tasks 4.1 and 4.5 remain open for their original
reasons. This retrospective does not alter historical performance claims.

## Validation and independent review

The read-only independent reviewer agreed that both reference discrepancies were
recorded. Its two corrections were applied: bridge status now says
`not-established-in-recorded-run`, and custody verification checks exact source
bindings, theorem selections and observed evidence pointers. Four mutation
controls pass. All 31 pinned source identities and eight case records verify.
The public reporting proposal has two expected failures and one passing control;
production functionality has not been changed to satisfy it. Strict OpenSpec
validation passes. The original workspace verifier confirms all 2,670 primary
files and 416 runtime inputs remain unchanged. Details are in `validation.json`.
