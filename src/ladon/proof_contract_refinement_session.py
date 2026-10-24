"""Bounded exact rational searches across cumulative refinement branches."""

from __future__ import annotations

import copy
from pathlib import Path

from ladon import proof_contract_refinement as branches
from ladon import rational_witness as rational

_SCHEMA = "ladon-rational-refinement-session-v1"
_NONCLAIMS = [
    "A counterexample applies only to the encoded goal and assignment.",
    "Refinement checks do not certify source formula fidelity.",
    "A proposed repair is not evidence for the original claim.",
    "Survival of a declared finite family does not establish universal truth.",
]


def create_refinement_branch(parent, constraints, *, source_root):
    """Expose the existing validator at the session's transition boundary."""
    return branches.create_refinement_branch(
        parent, constraints, source_root=source_root
    )


def _cap(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an integer from {low} through {high}")


def _source_root(value):
    try:
        path = Path(value)
    except (TypeError, ValueError) as error:
        raise ValueError("source_root must name an existing directory") from error
    return branches.SourceReader(path).root


def _derived_goal(goal, branch):
    result = copy.deepcopy(goal)
    result["premises"].extend(
        copy.deepcopy([item["expression"] for item in branch["constraints"]])
    )
    rational.validate_goal(result)
    return result


def _finding(finding_id, search):
    row = next(row for row in search["trace"] if row["status"] == "counterexample")
    witness = {
        "status": "abstract-countermodel",
        "assignment": copy.deepcopy(row["assignment"]),
        "goalSha256": search["goalSha256"],
        "evidence": copy.deepcopy(row),
    }
    return {
        "id": finding_id,
        "status": "abstract-countermodel",
        "discrepancy": {
            "kind": "exact-rational-counterexample",
            "goalSha256": search["goalSha256"],
        },
        "witness": witness,
    }


def _branch_check(branch, goal, assignment, source_root):
    return branches.check_rational_refinement(
        branch, goal, assignment, source_root=source_root
    )


def _search_round(goal, candidates, candidate_limit, reduction_limit, deadline, round_index):
    search = rational.search_candidates(
        goal, candidates, max_candidates=candidate_limit,
        deadline_monotonic=deadline, capture_invalid=True,
    )
    minimizing = None
    if search["status"] == "abstract-countermodel":
        row = next(row for row in search["trace"] if row["status"] == "counterexample")
        minimizing = rational.minimize_counterexample(
            goal, candidates, row["assignment"],
            max_reductions=reduction_limit, deadline_monotonic=deadline,
            capture_invalid=True,
        )
    return {
        "round": round_index,
        "candidateSearch": search,
        "minimization": minimizing,
    }


def _stage_stop(row):
    status = row["candidateSearch"]["status"]
    search_stops = {
        "invalid-input": ("invalid-input", "candidate-evaluation"),
        "deadline-exhausted": ("deadline-exhausted", "deadline"),
        "budget-exhausted": ("budget-exhausted", "candidate-cap"),
        "survived-declared-scope": ("survived-declared-scope", None),
    }
    if status in search_stops:
        return search_stops[status]
    minimization_stops = {
        "invalid-input": ("invalid-input", "reduction-evaluation"),
        "deadline-exhausted": ("deadline-exhausted", "deadline"),
        "budget-exhausted": ("budget-exhausted", "reduction-cap"),
    }
    return minimization_stops.get(row["minimization"]["status"])


def _search_stop(row, index, step_count, max_rounds):
    stage_stop = _stage_stop(row)
    if stage_stop is not None:
        return stage_stop
    if index >= step_count:
        return "abstract-countermodel", None
    if index + 1 >= max_rounds:
        return "budget-exhausted", "round-cap"
    return None


def _transition(current_branch, original, constraints, goal, witness, source_root, deadline):
    if rational._deadline_reached(deadline):
        return current_branch, None, "deadline-exhausted", "deadline", None, False
    parent = original if current_branch is None else current_branch
    try:
        branch = create_refinement_branch(parent, constraints, source_root=source_root)
    except (ValueError, TypeError, OSError) as error:
        return current_branch, None, "invalid-input", "branch-validation", str(error), False
    if rational._deadline_reached(deadline):
        return branch, None, "deadline-exhausted", "deadline", None, False
    try:
        check = _branch_check(branch, goal, witness, source_root)
    except (ValueError, TypeError, OSError) as error:
        return branch, None, "invalid-input", "branch-validation", str(error), True
    if rational._deadline_reached(deadline):
        return branch, check, "deadline-exhausted", "deadline", None, True
    return branch, check, None, None, None, True


def _append_witness(witnesses, row, round_index, original, finding_id):
    minimizing = row["minimization"]
    if minimizing is None:
        return original, 0, 0
    search_witness = next(
        item["assignment"] for item in row["candidateSearch"]["trace"]
        if item["status"] == "counterexample"
    )
    assignment = minimizing["assignment"] if minimizing["assignmentChecked"] else search_witness
    witnesses.append({
        "round": round_index, "assignment": copy.deepcopy(assignment),
        "goalSha256": row["candidateSearch"]["goalSha256"],
        "branchId": row["branch"]["id"] if row["branch"] else None,
        "searchTrace": copy.deepcopy(row["candidateSearch"]["trace"]),
        "minimization": copy.deepcopy(minimizing),
    })
    if original is None:
        original = _finding(finding_id, row["candidateSearch"])
    rechecked = minimizing.get("initialCheckAttempted", minimizing["assignmentChecked"])
    return original, int(rechecked), minimizing["attemptCount"]


def _work_stop(state, limits):
    deadline, max_candidates, max_reductions, _max_rounds = limits
    if rational._deadline_reached(deadline):
        return "deadline-exhausted", "deadline"
    if state["candidateChecks"] >= max_candidates:
        return "budget-exhausted", "candidate-cap"
    if state["reductions"] >= max_reductions:
        return "budget-exhausted", "reduction-cap"
    return None


def _advance_round(state, index, limits, inputs):
    deadline, max_candidates, max_reductions, max_rounds = limits
    goal, candidates, steps, source_root, finding_id = inputs
    stopping = _work_stop(state, limits)
    if stopping is not None:
        state["status"], state["stopReason"] = stopping
        return False
    current_goal = goal if state["branch"] is None else _derived_goal(goal, state["branch"])
    row = _search_round(
        current_goal, candidates, max_candidates - state["candidateChecks"],
        max_reductions - state["reductions"], deadline, index + 1,
    )
    row["branch"] = copy.deepcopy(state["branch"])
    row["branchCheck"] = copy.deepcopy(state["branchCheck"])
    state["rounds"].append(row)
    search = row["candidateSearch"]
    state["candidateChecks"] += search["attemptedCount"]
    state["original"], checked, reduced = _append_witness(
        state["witnesses"], row, index + 1, state["original"], finding_id
    )
    state["minimizationRechecks"] += checked
    state["reductions"] += reduced
    stopping = _search_stop(row, index, len(steps), max_rounds) or _work_stop(state, limits)
    if stopping is not None:
        state["status"], state["stopReason"] = stopping
        return False
    return _apply_transition(state, index, goal, steps, source_root, deadline)


def _apply_transition(state, index, goal, steps, source_root, deadline):
    branch, check, status, reason, message, attempted = _transition(
        state["branch"], state["original"], steps[index], goal,
        state["witnesses"][-1]["assignment"], source_root, deadline,
    )
    state["branch"] = branch
    state["transitionCheckAttempts"] += int(attempted)
    if check is not None:
        state["transitionChecks"] += 1
        state["branchCheck"] = check
    if status is not None:
        state["rounds"][-1]["pendingBranch"] = copy.deepcopy(branch)
        state["rounds"][-1]["pendingBranchCheck"] = copy.deepcopy(check)
        if message is not None:
            state["rounds"][-1]["branchError"] = message
        state["status"], state["stopReason"] = status, reason
        return False
    return True


def _result(state, deadline, max_rounds, max_candidates, max_reductions):
    original = state["original"]
    rounds = state["rounds"]
    result = {
        "schema": _SCHEMA,
        "status": state["status"],
        "stopReason": state["stopReason"],
        "roundCount": sum(bool(row["candidateSearch"]["attemptedCount"]) for row in rounds),
        "roundLimit": max_rounds,
        "candidateChecks": state["candidateChecks"],
        "candidateLimit": max_candidates,
        "reductionAttempts": state["reductions"],
        "reductionLimit": max_reductions,
        "transitionChecks": state["transitionChecks"],
        "transitionCheckAttempts": state["transitionCheckAttempts"],
        "transitionCheckLimit": max_rounds - 1,
        "minimizationRechecks": state["minimizationRechecks"],
        "minimizationRecheckLimit": max_rounds,
        "deadlineMonotonic": deadline,
        "originalFinding": original,
        "witnessHistory": state["witnesses"],
        "rounds": rounds,
        "originalClaimRefuted": False,
        "sourceFormulaFidelity": "unverified",
        "finiteSurvival": _finite_survival(state["status"], rounds),
        "nonclaims": list(_NONCLAIMS),
    }
    return copy.deepcopy(result)


def _finite_survival(status, rounds):
    if status != "survived-declared-scope" or not rounds:
        return None
    search = rounds[-1]["candidateSearch"]
    return {"goalSha256": search["goalSha256"], "familySize": search["familySize"]}


def run_rational_refinement_session(
    goal,
    candidate_lists,
    refinement_steps,
    *,
    source_root,
    finding_id,
    deadline_monotonic,
    max_candidates=256,
    max_reductions=32,
    max_rounds=4,
):
    """Search a base goal and up to three supplied cumulative rational refinements.

    Work limits and one absolute deadline apply to the entire call. Source
    validation and exact arithmetic are cooperative atomic operations; the next
    stage checks the same deadline. No source lift or spuriousness is inferred.
    """
    _cap(max_candidates, 1, 256, "candidate cap")
    _cap(max_reductions, 1, 32, "reduction cap")
    _cap(max_rounds, 1, 4, "round cap")
    if type(refinement_steps) is not list or len(refinement_steps) > 3:
        raise ValueError("refinement_steps must be a list of at most three batches")
    branches._text(finding_id, "finding_id", 128)
    if deadline_monotonic is None:
        raise ValueError("session deadline must be finite")
    deadline = rational._validated_deadline(deadline_monotonic)
    source_root = _source_root(source_root)
    goal_copy = branches._bounded_json(goal, "goal")
    candidate_copy = branches._bounded_json(candidate_lists, "candidate lists")
    steps_copy = branches._bounded_json(refinement_steps, "refinement steps")
    rational.validate_goal(goal_copy)
    # Validate candidate inputs before beginning work.
    rational._candidate_family(goal_copy["variables"], candidate_copy)
    if any(type(batch) is not list or not batch for batch in steps_copy):
        raise ValueError("each refinement batch must be a nonempty list")

    state = {
        "rounds": [], "witnesses": [], "candidateChecks": 0,
        "reductions": 0, "transitionChecks": 0, "transitionCheckAttempts": 0,
        "minimizationRechecks": 0,
        "branch": None, "branchCheck": None, "original": None,
        "status": "survived-declared-scope", "stopReason": None,
    }
    limits = (deadline, max_candidates, max_reductions, max_rounds)
    inputs = (goal_copy, candidate_copy, steps_copy, source_root, finding_id)
    _run_rounds(state, limits, inputs)
    return _result(state, deadline, max_rounds, max_candidates, max_reductions)


def _run_rounds(state, limits, inputs):
    max_rounds = limits[3]
    step_count = len(inputs[2])
    for index in range(min(max_rounds, step_count + 1)):
        if not _advance_round(state, index, limits, inputs):
            break
