# Rational branch Lean checks

`ladon.proof_contract_rational_probes.plan_rational_branch_probe` plans a
validated rational refinement branch at one exact assignment. The separate
`check_rational_branch_probe` API checks supplied Lean terms against those
regenerated propositions. This is separate from the ordinary paired
application-probe route and currently has no CLI command.

The closed request contains exactly `sourceRoot`, `workspaceRoot`, `branch`,
`baseGoal`, `assignment`, `deadlineMonotonic`, and `limits`. `sourceRoot` is the
root used to validate source citations. `workspaceRoot` selects the pinned Lean
toolchain and already-built Mathlib. The roots are intentionally independent.
`deadlineMonotonic` is an absolute deadline from Python's monotonic clock. The
optional limit keys are `timeout_seconds`, `max_output_bytes`, and
`max_rss_bytes`; omitted values use bounded defaults.

```python
import time
from ladon.proof_contract_rational_probes import (
    check_rational_branch_probe,
    plan_rational_branch_probe,
)

request = {
    "sourceRoot": "/path/to/source-project",
    "workspaceRoot": "/path/to/pinned-lean-workspace",
    "branch": validated_branch,
    "baseGoal": validated_rational_goal,
    "assignment": {"x": "2"},
    "deadlineMonotonic": time.monotonic() + 300,
    "limits": {
        "timeout_seconds": 30,
        "max_output_bytes": 8 * 1024 * 1024,
        "max_rss_bytes": 12 * 1024**3,
    },
}
plan = plan_rational_branch_probe(request)
if plan["status"] == "planned":
    proofs = {goal["goalId"]: "by norm_num" for goal in plan["goals"]}
    checked = check_rational_branch_probe(request, plan["planId"], proofs)
```

Planning runs the rational branch checker, regenerates one closed Lean
proposition per evaluated premise and conclusion, then preflights them with
Mathlib `norm_num`. Native ProofIR validation recomputes the generated
obligations from the derived goal and assignment before accepting the plan.
The plan ID binds branch and source-span identities, base and derived goals,
assignment, proposition digests, checker identity, and a workspace identity
that includes the pin-selected Lean executable digest and compiled library
roots. A completed check receipt additionally binds the digest of the exact
compiled-module inventory loaded during proof checking and rejects if that
inventory changes between generated goals.

`check_rational_branch_probe(request, planId, terms, cached_result=None)`
regenerates the plan and rejects stale IDs. `terms` must contain one bounded,
nonempty proof for every regenerated goal ID. Each proof is checked in an
isolated temporary Lean source root sharing the selected compiled Mathlib
roots. The target workspace is not modified. Ladon captures each generated
closed goal, checks the term, independently replays the closed declaration,
and collects its transitive axioms. It reports checked support only when
completion, replay, and the no-placeholder trust policy all pass. It emits a
separate `proofir.check-run` artifact for every accepted goal, plus a checked
`proofir.contract-analysis` artifact at stage `rational-branch-check`. That
artifact references the exact plan and every goal check-run. Native batch
validation verifies each run's rational binding against the regenerated plan,
including goal text, term digest, checker identity, and compiled-module
inventory. It also requires complete no-placeholder trust coverage and rejects
axioms outside Ladon's declared standard axiom set. The plan retains the immutable branch record, verifies that its
digest and original finding ID agree, reconstructs the derived goal from the
base goal plus the exact branch constraints, and recomputes source-span
identities from cited constraints. When attached to an investigation
observation, the checked artifact's original finding ID must match the
observation ID. Consumers must retain the plan, check-runs, and checked analysis
artifact together for reference closure.

The checking worker is bounded to at most 120 seconds and 12 GiB per goal,
subject to the request's shared deadline and stricter limits. Timeout, memory,
output, unsupported, rejected, or stale outcomes publish no checked support.

The optional `cached_result` is currently informational only. Cache entries
have no authenticated provenance, so every supplied proof term is freshly
captured, completed, independently replayed, and trust-checked by Lean. A cache
cannot authorize checked support or skip the worker. This deliberately leaves
cache-based acceleration disabled until Ladon has a provenance mechanism that
callers cannot forge.

These propositions decide the bounded AST at one finite rational assignment.
A checked result does not establish source-prose fidelity or universal truth,
and does not prove or refute the original theorem. Division by zero is rejected
before goal generation; a missing or incompatible Mathlib workspace reports
`unsupported`. The investigation report carries the checked artifact as
attached evidence but keeps route support and mathematical falsity
`not-established` until source fidelity and theorem-level relationships have
their own checks. See the [native artifact tests](../tests/test_rational_branch_checked_artifact.py),
[projection tests](../tests/test_rational_branch_checked_reporting.py),
[receipt tests](../tests/test_rational_branch_receipts_v3.py), and
[plan tests](../tests/test_rational_branch_plan_v8.py) for the current contracts.

## Finite refinement sessions (Python API)

`ladon.proof_contract_refinement_session.run_rational_refinement_session`
searches a declared rational family, then applies supplied constraint batches
only after finding a countermodel. Every new branch accumulates the predicates
as premises in the next goal. The first finding, every search trace, and the
later witnesses remain available in the result. These sessions use exact
Python rational arithmetic; the separate Lean plan/check API above can check a
returned branch at a chosen assignment.

```python
import time
from ladon.proof_contract_refinement_session import run_rational_refinement_session

goal = {
    "variables": ["x"],
    "premises": [],
    "conclusion": {"op": "ge", "left": {"var": "x"}, "right": {"rat": 2}},
}
steps = [
    [{
        "id": f"bound-{bound}",
        "expression": {"op": "ge", "left": {"var": "x"}, "right": {"rat": bound}},
        "justification": {"kind": "proposed-repair", "rationale": "Try this extra bound."},
    }]
    for bound in (1, 2)
]
result = run_rational_refinement_session(
    goal, {"x": [0, 1, 2, 3]}, steps,
    source_root=".", finding_id="example-finding",
    deadline_monotonic=time.monotonic() + 10,
)
assert result["status"] == "survived-declared-scope"
assert result["roundCount"] == 3
assert result["originalFinding"]["witness"]["assignment"] == {"x": "0"}
```

Here the original and intermediate goals have witnesses `x = 0` and `x = 1`.
The final goal survives the four declared assignments after adding `x >= 2`.
Both added constraints are labeled proposed repairs; survival does not resolve
the original finding or establish universal truth. Source-cited constraints
use the existing branch justification format and retain unverified formula
fidelity. The session does not infer constraints, construct source-level lifts,
or prove that a witness is spurious.

One call shares `max_candidates` (1–256), `max_reductions` (1–32),
`max_rounds` (1–4, including the initial search), and the original absolute
deadline. At most three nonempty constraint batches are accepted. Initial
minimizer rechecks and transition-check attempts are counted separately and
bounded by the round limit. `transitionChecks` counts completed checks;
`transitionCheckAttempts` also counts attempts rejected during validation.
Source validation and individual arithmetic checks are synchronous: deadlines
are checked at stage boundaries, without interrupting an operation already in
progress. Completed checks remain in the history when a deadline expires.

Exhaustion stops the session with its checked prefix, last checked witnesses,
and incomplete minimization evidence. Reached stale citations or undefined
arithmetic return `invalid-input` with earlier evidence retained. Malformed
outer inputs and limits raise before work. There is no implicit resume or new
clock inside a call. The source root is validated as an existing directory and
resolved once at entry, so later working-directory changes cannot rebind it.
The result is local search evidence. The separate source-owned checking API
below handles the bounded natural-number interpretation; CLI integration remains open.

## Source-to-formal lift obligations (planning API)

`ladon.proof_contract_lift_goals.plan_nat_rational_lift(goal, witness,
interpretation, mode="realization")` generates explicit obligations for a
single natural-number object mapped to an exact rational value. `mode` may
also be `"incompatibility"`. The witness must actually refute the supplied
rational implication under every premise; a caller's status label is insufficient.

The interpretation has the following shape:

```python
interpretation = {
    "profile": "nat-cast-v1",
    "source": {"path": "Fixture.lean", "sha256": "<64 lowercase hex characters>"},
    "formalClaim": "LiftFixture.Claim",
    "formalPredicate": "LiftFixture.Predicate",
}
```

The generated conjunction requires equivalence of the complete formal claim
with `∀ n : Nat, Predicate n`, then pointwise equivalence of `Predicate n`
with the rational implication at the canonical cast of `n`. A realization
must supply an object mapping to the exact witness value, refute its predicate,
and prove the negation of the complete formal claim. Incompatibility instead
requires a proof that the exact rational value has no natural-number preimage.
All original premises remain in the implication. Division expressions, multiple
variables, and other domain profiles currently return explicit unsupported plans.

Plans bind the full input representations, source reference, interpretation,
mode, and generated formulas in `planId`. They do not read the source, verify
the interpretation, or accept proof receipts. `sourceVerified` and
`originalClaimRefuted` remain false; `liftStatus` is `pending-checks` for a
generated plan. This API supplies obligations, not a positive public lift result.

The constructed native feasibility experiment uses the local Ladon checkout
and the installed Lean 4.33.0 toolchain:

```bash
PYTHONPATH=src python scripts/check_nat_rational_lift_feasibility.py \
  --output .codex/state/my-lift-feasibility
```

The output directory must be new. Six cases share a 30-minute deadline and
12 GiB RSS cap, with a 120-second cap per supervised checker call. A resource
stop ends the experiment. No network access, build, or automatic retry occurs.
The optional `--deadline-monotonic` carries an earlier absolute deadline on
the same host and can only shorten the available time. The experiment preserves
plans, proof terms, source, raw checker evidence, and the initial/final records.
It checks realization, range incompatibility, unsupported interpretation, and
changed-witness, omitted-assumption, and admitted-proof controls. These are
constructed source examples; they do not measure unfamiliar-paper detection.

## Fresh source-owned lift checks

`ladon.proof_contract_lift_check.check_nat_rational_lift(request, plan_id, term)`
regenerates the plan, reads and verifies its source, and runs fresh Lean capture,
completion, independent replay and axiom checks. It accepts no cached receipt or
caller-supplied checker. A request contains exactly:

```python
request = {
    "repoRoot": str(repo_root),
    "goal": goal,
    "witness": witness,
    "interpretation": interpretation,
    "mode": "realization",  # or "incompatibility"
    "deadlineMonotonic": shared_deadline,
    "limits": {},
}
result = check_nat_rational_lift(request, plan["planId"], proof_term)
```

The outcomes distinguish `lifted-counterexample`, `spurious-countermodel`, and
`unsupported`. A failed proof remains rejected or unresolved. Positive results
retain the original witness and bind the exact source, goal, term, attempt,
checker and Lean environment. Only a checked realization sets
`formalClaimRefuted`; `originalClaimRefuted` always stays false and
`sourceFormulaFidelity` stays `unverified`. These are local Ladon results, not
authenticated certificates for accepting arbitrary imported JSON.

The checker compares the elaborated proposition with an independent clean Rat
proposition. This catches source-defined instances that change a numeral or
operator's meaning. The clean observation uses opaque names for the selected
claim and predicate; the proof itself runs against their actual definitions.
Unavailable canonical elaboration or import coverage remains unsupported.

Each attempt is capped at 120 seconds, 12 GiB process-tree RSS and 8 MiB output,
under the caller's original absolute deadline. Lower limits are supported;
timeout/RSS requests above the caps are clamped and oversized output limits are
rejected. Resource exhaustion preserves the witness and stops progress without
an automatic retry. Unsupported plans accept `term=None` and start no Lean process.

The public-API qualification adds an altered-numeral control to the six earlier cases:

```bash
PYTHONPATH=src python scripts/check_public_nat_rational_lift.py \
  --output .codex/state/a-new-public-lift-check
```

All seven cases share one 30-minute clock. This constructed evaluation checks
the API boundary; detection benefit on unfamiliar papers remains unmeasured.
