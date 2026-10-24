# Native source-to-formal lift feasibility

Historical precursor: the production owner subsequently passed the
[public lift-check acceptance gate](public-lift-check.md), closing Task 1.3.
The remaining-acceptance section below records the boundary at this earlier stage.

## Implemented boundary

`src/ladon/proof_contract_lift_goals.py` generates bounded obligations from an
exact rational countermodel, an explicit source reference and two formal names.
It checks every abstract premise, keeps input representations immutable, and
binds the complete inputs and formulas in a deterministic identity. It remains
a planning API: source references are unverified, positive lift classifications
are unavailable, and `originalClaimRefuted` remains false.

The single-object profile maps `n : Nat` through `Rat.ofInt (Int.ofNat n)`.
Before either outcome, it requires both:

1. Equivalence of the selected complete formal claim and `∀ n, P n`.
2. Pointwise equivalence of `P n` and the complete abstract implication at the
   mapped object, retaining every premise and the conclusion.

Realization additionally requires `∃ n, cast n = q ∧ ¬ P n` and the negation
of the selected complete formal claim. Range incompatibility requires
`¬ ∃ n, cast n = q`. Thus a closed rational assignment does not become a
source-level result merely because a reviewer labels it realizable or spurious.
Division ASTs, multiple variables and analytical profiles are unsupported.

The fixture `tests/fixtures/proof_contract_lifting/Fixture.lean` defines
`P n := n < 2 → n = 0` and its universally quantified claim. Its stricter control
includes an extra `n = 0` assumption. The runner uses installed Lean 4.33.0 and
the checkout's existing supervised source-goal capture, completion, independent
replay and axiom-policy checks. No Mathlib build, online lookup, dependency
addition or change to the original public classifier is involved.

## Native qualification and preserved first result

The first run is preserved in
`.codex/state/refinement-lift/native-gate-01/`. It completed all six cases in
134.139 seconds under one 1,800-second absolute deadline and a 12 GiB RSS cap.
Both positive formal goals had accepted independent replay and complete trust
coverage. Unsupported remained unsupported; every negative was refused.

Its `RESULT.json` nevertheless records **5/6 and `passed: false`**. The
changed-witness control expected a type-check rejection but received a trust
rejection: Lean's recovered term depended on `sorryAx`, which the existing
policy rejected. Independent review #1232 rejected that recorded gate and
required a corrected rerun. The original report and all raw checks remain intact.

Root added and observed 13 failing grading/deadline regressions before correcting
the runner. A proof-negative control accepts only concrete `rejected` or
`trust-rejected`, retaining the exact observed category; unsupported, unresolved,
and resource failures cannot pass it. The explicit admitted-proof control still
requires trust rejection. The rerun in `native-gate-02` uses the **same absolute
deadline from gate-01**, with no clock reset. Its final evidence and independent
follow-up acceptance are recorded below.

## Accepted bounded result

Independent follow-up review **#1240** accepted the planner and constructed
native feasibility slice. Gate-02 passed **6/6** in **129.098 seconds**:

| Case | Exact observed outcome |
| --- | --- |
| Realization at `q = 1` | Checked, accepted replay and complete trusted axiom coverage |
| Incompatibility at `q = -1` | Checked, accepted replay and complete trusted axiom coverage |
| Analytical profile | Unsupported, no native proof attempted |
| Changed witness `q = 1/2` with the old proof | Trust rejected for `sorryAx` |
| Omitted original assumption | Proof rejected |
| Admitted proof | Trust rejected for `sorryAx` |

The source remained unchanged and neither run had a resource stop. Both start
records use absolute monotonic deadline `2291831.29564263`. Combined native
execution took **263.237 seconds**; wall time from the first run's start through
the second run's completion, including correction and testing, was **416.424
seconds**. Maximum reported RSS across the two runs was **3,812,868,096 bytes
(3.551 GiB)**, within the 12 GiB cap. The [versioned evidence manifest](native-lift-feasibility-results.json)
records both results, timestamps, input identities, artifact hashes and local
raw-evidence locations. The initial failed qualification is retained alongside
the accepted second run.

Verification:

- **206 passed, 1 slow integration skipped** across the rational refinement,
  witness, branch identity/receipt/reporting and new lifting selections.
- **34 new tests** cover planner boundaries and experiment grading/shared
  deadlines; independent review reran them successfully.
- Scoped `scripts/python_quality.py` passed Ruff, Radon and Vulture; all changed
  Python functions are at most complexity B. `strict_quality_issues` returned
  no issues for the four new Python files; compilation also passed.
- Both new active test files match their frozen hashes. The registry still
  has the previously recorded unrelated mismatch in
  `tests/test_rational_lean_encoder_v2.py`; this is not a repository-wide
  verification claim. The reviewed test-helper refactor preserved every
  assertion AST and its earlier frozen versions remain recorded.

Reproduction uses the local checkout:

```bash
PYTHONPATH=src python scripts/check_nat_rational_lift_feasibility.py \
  --output .codex/state/a-new-lift-feasibility
```

The retained second run additionally passed
`--deadline-monotonic 2291831.29564263`, taken from the first run's `start.json`.
That historical number is not reusable on another host or after its deadline.

## Remaining acceptance

Task 1.3 remains open. The constructed experiment does not provide a production
API that regenerates an exact plan, verifies source and environment identity,
runs the checks, and owns a lifted/incompatible/unsupported result. That owner
must reject stale or substituted evidence and preserve resource-stop semantics.
It must also distinguish refuting the selected formal interpretation from
refuting the manuscript's intended claim. Task 3.1 then needs the public
refine/inspect and original/revised report workflow.

This is implementation feasibility for an explicit small interpretation.
It does not establish prose fidelity, generic function-space lifting, theorem
falsity in Navier–Stokes, or improved detection on unfamiliar source material.
