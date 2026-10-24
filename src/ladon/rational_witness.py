"""Exact, bounded rational arithmetic for checking candidate local witnesses.

A successful check is a counterexample to the encoded implication only when all
premises hold and the conclusion fails. Other outcomes make no truth claim.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
import time
from fractions import Fraction
from typing import Any

_SCHEMA = "ladon-rational-witness-v1"
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,31}\Z", re.ASCII)
_LITERAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?\Z", re.ASCII)
_MAX_BITS = 4096
_MAX_NODES = 4096
_MAX_DEPTH = 32
_MAX_GOAL_BYTES = 1024 * 1024
_monotonic = time.monotonic


def _fail(message: str) -> None:
    raise ValueError(message)


def _literal(value: Any) -> Fraction:
    if isinstance(value, bool):
        _fail("boolean is not a rational literal")
    if type(value) is int:
        if value.bit_length() > 426 or len(str(value)) > 128:
            _fail("rational literal exceeds 128 characters")
        result = Fraction(value)
    elif type(value) is str:
        if len(value) > 128 or not _LITERAL.fullmatch(value):
            _fail("invalid rational literal")
        try:
            if "/" in value:
                numerator, denominator = value.split("/", 1)
                result = Fraction(int(numerator), int(denominator))
            else:
                result = Fraction(int(value), 1)
        except (ValueError, ZeroDivisionError):
            _fail("invalid rational literal")
    else:
        _fail("rational literal must be an integer or string")
    _bounded(result)
    return result


def _bounded(value: Fraction) -> Fraction:
    if value.numerator.bit_length() > _MAX_BITS or value.denominator.bit_length() > _MAX_BITS:
        _fail("rational intermediate exceeds 4096 bits")
    return value


def _canonical(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _mapping(value: Any, keys: set[str], what: str) -> dict:
    if type(value) is not dict:
        _fail(f"{what} must use a JSON-native object")
    if set(value) != keys:
        _fail(f"{what} has invalid shape")
    return value


def _predicate_shape(value: Any) -> None:
    p = _mapping(value, {"op", "left", "right"}, "predicate")
    if type(p["op"]) is not str or p["op"] not in {"le", "lt", "eq", "ne", "ge", "gt"}:
        _fail("unknown predicate operator")


def _count_node(count: list[int], depth: int) -> None:
    count[0] += 1
    if count[0] > _MAX_NODES:
        _fail("goal exceeds 4096 AST nodes")
    if depth > _MAX_DEPTH:
        _fail("expression depth exceeds 32")


def _expression_shape(value: Any, names: set[str], depth: int, count: list[int]) -> None:
    _count_node(count, depth)
    if type(value) is not dict:
        _fail("expression must be an object")
    keys = set(value)
    if keys == {"var"}:
        _variable_shape(value["var"], names)
    elif keys == {"rat"}:
        _literal(value["rat"])
    elif keys == {"op", "args"}:
        _operator_shape(value, names, depth, count)
    elif keys == {"op", "args", "exponent"}:
        _power_shape(value, names, depth, count)
    else:
        _fail("invalid expression shape")


def _variable_shape(name: Any, names: set[str]) -> None:
    if type(name) is not str or not _NAME.fullmatch(name) or name not in names:
        _fail("unknown variable")


def _operator_shape(value: dict, names: set[str], depth: int, count: list[int]) -> None:
    op, args = value["op"], value["args"]
    if type(args) is not list:
        _fail("operator arguments must be a list")
    if type(op) is not str:
        _fail("unknown expression operator")
    if op in {"add", "sub", "mul", "div"}:
        arity = 2
    elif op in {"neg", "abs"}:
        arity = 1
    else:
        _fail("unknown expression operator")
    if len(args) != arity:
        _fail("wrong operator arity")
    for arg in args:
        _expression_shape(arg, names, depth + 1, count)


def _power_shape(value: dict, names: set[str], depth: int, count: list[int]) -> None:
    if value["op"] != "pow" or type(value["args"]) is not list or len(value["args"]) != 1:
        _fail("invalid power expression")
    exponent = value["exponent"]
    if type(exponent) is not int or not 0 <= exponent <= 8:
        _fail("power exponent must be an integer from 0 through 8")
    _expression_shape(value["args"][0], names, depth + 1, count)


def _variables_shape(variables: Any) -> None:
    if type(variables) is not list or len(variables) > 32:
        _fail("variables must be a list of at most 32 names")
    if any(type(n) is not str or not _NAME.fullmatch(n) for n in variables):
        _fail("invalid variable name")
    if len(set(variables)) != len(variables):
        _fail("variable names must be unique")


def _goal_shape(goal: Any) -> tuple[list[str], list[Any], Any]:
    g = _mapping(goal, {"variables", "premises", "conclusion"}, "goal")
    variables, premises = g["variables"], g["premises"]
    _variables_shape(variables)
    if type(premises) is not list or len(premises) > 64:
        _fail("premises must be a list of at most 64 predicates")
    _predicate_shape(g["conclusion"])
    for p in premises:
        _predicate_shape(p)
    names, count = set(variables), [0]
    # Count predicate nodes as well as all expression nodes.
    for p in [*premises, g["conclusion"]]:
        _count_node(count, 0)
        _expression_shape(p["left"], names, 1, count)
        _expression_shape(p["right"], names, 1, count)
    return variables, premises, g["conclusion"]


def validate_goal(goal: Any) -> None:
    """Validate the complete bounded goal without assigning its variables."""
    _goal_shape(goal)


def _eval(expr: dict, env: dict[str, Fraction]) -> Fraction:
    if "var" in expr:
        return env[expr["var"]]
    if "rat" in expr:
        return _literal(expr["rat"])
    op, args = expr["op"], expr["args"]
    values = [_eval(arg, env) for arg in args]
    return _bounded(_apply_operator(op, values, expr))


def _apply_operator(op: str, values: list[Fraction], expr: dict) -> Fraction:
    if op == "add":
        return values[0] + values[1]
    if op == "sub":
        return values[0] - values[1]
    if op == "mul":
        return values[0] * values[1]
    if op == "div":
        if values[1] == 0:
            _fail("division by zero")
        return values[0] / values[1]
    if op == "neg":
        return -values[0]
    if op == "abs":
        return abs(values[0])
    return values[0] ** expr["exponent"]  # pow was validated


def _check_predicate(predicate: dict, env: dict[str, Fraction]) -> dict:
    left, right = _eval(predicate["left"], env), _eval(predicate["right"], env)
    op = predicate["op"]
    holds = {
        "le": left <= right,
        "lt": left < right,
        "eq": left == right,
        "ne": left != right,
        "ge": left >= right,
        "gt": left > right,
    }[op]
    return {"op": op, "lhs": _canonical(left), "rhs": _canonical(right), "holds": holds}


def check_witness(goal: Any, assignment: Any) -> dict:
    """Check one exact assignment; never infer universal validity from failure."""
    variables, premises, conclusion = _goal_shape(goal)
    if type(assignment) is not dict or set(assignment) != set(variables):
        _fail("assignment must bind exactly every goal variable")
    env = {name: _literal(assignment[name]) for name in variables}
    # Evaluate every premise and the conclusion, even after a false premise.
    premise_results = [_check_predicate(p, env) for p in premises]
    conclusion_result = _check_predicate(conclusion, env)
    if not all(result["holds"] for result in premise_results):
        status = "outside-assumptions"
    elif not conclusion_result["holds"]:
        status = "counterexample"
    else:
        status = "not-counterexample"
    return {
        "schema": _SCHEMA,
        "status": status,
        "premises": premise_results,
        "conclusion": conclusion_result,
        "nonclaims": [
            "A counterexample applies only to the encoded goal and assignment.",
            "Outside-assumptions is not a counterexample to the implication.",
            "Not-counterexample does not establish universal truth.",
        ],
    }


def _candidate_family(variables, candidate_lists):
    if type(candidate_lists) is not dict or set(candidate_lists) != set(variables):
        _fail("candidate lists must name exactly every goal variable")
    domains, declared = [], {}
    total_values, family_size = 0, 1
    for name in variables:
        values = candidate_lists[name]
        if type(values) is not list or not values or len(values) > 256:
            _fail("each candidate list must contain 1 through 256 rational values")
        total_values += len(values)
        if total_values > 4096:
            _fail("candidate lists exceed 4096 values")
        domain = [_canonical(_literal(value)) for value in values]
        if len(set(domain)) != len(domain):
            _fail("candidate lists must not repeat equivalent rational values")
        domains.append(domain)
        declared[name] = list(values)
        family_size *= len(values)
    return domains, declared, family_size


def _goal_identity(goal):
    encoded = json.dumps(goal, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(encoded) > _MAX_GOAL_BYTES:
        _fail("encoded rational goal exceeds 1 MiB")
    return json.loads(encoded), hashlib.sha256(encoded).hexdigest()


def _candidate_check(goal, variables, values, *, capture_invalid=False):
    assignment = dict(zip(variables, values, strict=True))
    try:
        checked = check_witness(goal, assignment)
    except ValueError as error:
        if not capture_invalid:
            raise
        return {"assignment": assignment, "status": "invalid-input", "error": str(error)}, None
    row = {"assignment": assignment, "status": checked["status"]}
    summary = {
        "premisesHold": [item["holds"] for item in checked["premises"]],
        "conclusionHolds": checked["conclusion"]["holds"],
    }
    return row, summary


def _run_candidate_search(
    goal, variables, domains, max_candidates, deadline_monotonic=None,
    *, capture_invalid=False,
):
    products = itertools.product(*domains) if variables else [()]
    trace, checks = [], []
    found, deadline_exhausted = False, False
    for values in itertools.islice(products, max_candidates):
        if _deadline_reached(deadline_monotonic):
            deadline_exhausted = True
            break
        row, summary = _candidate_check(
            goal, variables, values, capture_invalid=capture_invalid
        )
        trace.append(row)
        checks.append(summary)
        if row["status"] == "invalid-input":
            break
        if row["status"] == "counterexample":
            found = True
            break
    return trace, checks, found, deadline_exhausted


def _deadline_reached(deadline_monotonic):
    return deadline_monotonic is not None and _monotonic() >= deadline_monotonic


def _scan_interrupted(
    trace, current, attempts, starting_attempts, reason, accepted=False, status=None
):
    trace.append({"result": "interrupted", "reason": reason})
    return current, attempts - starting_attempts, accepted, True, status or reason


def _accepted_reduction(attempt, attempts, starting_attempts, cap, trace, deadline):
    updated = attempt["assignment"]
    if attempts == cap:
        return _scan_interrupted(
            trace, updated, attempts, starting_attempts, "reduction-cap",
            accepted=True, status="budget-exhausted",
        )
    if _deadline_reached(deadline):
        return _scan_interrupted(
            trace, updated, attempts, starting_attempts, "deadline-exhausted",
            accepted=True,
        )
    return updated, attempts - starting_attempts, True, False, None


def _candidate_search_status(found, attempted, family_size, deadline_exhausted, invalid=False):
    if invalid:
        return "invalid-input"
    if found:
        return "abstract-countermodel"
    if attempted == family_size:
        return "survived-declared-scope"
    if deadline_exhausted:
        return "deadline-exhausted"
    return "budget-exhausted"


def search_candidates(
    goal: Any,
    candidate_lists: Any,
    *,
    max_candidates: int = 256,
    deadline_monotonic: float | None = None,
    capture_invalid: bool = False,
) -> dict:
    """Search one explicitly declared finite rational family, with no global claim.

    Candidate values use the goal variable order and the declared order within
    each domain. At most 256 assignments are checked. A completed search only
    establishes survival of that recorded finite family.

    With capture_invalid, undefined arithmetic produces a terminal invalid row
    and a null check summary, retaining the completed prefix. Default calls
    preserve their exception behavior.
    """
    if type(capture_invalid) is not bool:
        _fail("capture_invalid must be a boolean")
    variables, _premises, _conclusion = _goal_shape(goal)
    goal_snapshot, goal_digest = _goal_identity(goal)
    if type(max_candidates) is not int or not 1 <= max_candidates <= 256:
        _fail("candidate search cap must be an integer from 1 through 256")
    deadline_monotonic = _validated_deadline(deadline_monotonic)
    domains, declared, family_size = _candidate_family(variables, candidate_lists)
    trace, checks, found, deadline_exhausted = _run_candidate_search(
        goal_snapshot, variables, domains, max_candidates, deadline_monotonic,
        capture_invalid=capture_invalid,
    )
    attempted = len(trace)
    status = _candidate_search_status(
        found, attempted, family_size, deadline_exhausted,
        invalid=bool(trace and trace[-1]["status"] == "invalid-input"),
    )
    return {
        "schema": "ladon-rational-candidate-search-v1",
        "status": status,
        "goal": goal_snapshot,
        "goalSha256": goal_digest,
        "declaredFamily": declared,
        "familySize": family_size,
        "attemptedCount": attempted,
        "deadlineMonotonic": deadline_monotonic,
        "trace": trace,
        "checks": checks,
        "nonclaims": [
            "A counterexample applies only to the encoded goal and assignment.",
            "Survived-declared-scope does not establish universal truth.",
            "An abstract countermodel does not refute source prose without a checked lift.",
            "This finite rational search says nothing about candidates outside the declared family.",
        ],
    }


def _canonical_assignment(variables, assignment, domains):
    if type(assignment) is not dict or set(assignment) != set(variables):
        _fail("initial assignment must bind exactly every goal variable")
    result = {name: _canonical(_literal(assignment[name])) for name in variables}
    for name in variables:
        if result[name] not in domains[name]:
            _fail("initial assignment must use values from every declared candidate list")
    return result


def _rank_sum(variables, domains, assignment):
    return sum(domains[name].index(assignment[name]) for name in variables)


def _reduction_attempt(goal, variables, domains, current, name, *, capture_invalid=False):
    rank = domains[name].index(current[name])
    proposed = dict(current)
    proposed[name] = domains[name][rank - 1]
    try:
        checked = check_witness(goal, proposed)
    except ValueError as error:
        if not capture_invalid:
            raise
        return {
            "variable": name, "assignmentBefore": dict(current),
            "assignment": proposed,
            "measureBefore": _rank_sum(variables, domains, current),
            "measureAfter": _rank_sum(variables, domains, proposed),
            "result": "invalid-input", "accepted": False, "error": str(error),
        }
    accepted = checked["status"] == "counterexample"
    return {
        "variable": name,
        "assignmentBefore": dict(current),
        "assignment": proposed,
        "measureBefore": _rank_sum(variables, domains, current),
        "measureAfter": _rank_sum(variables, domains, proposed),
        "result": checked["status"],
        "accepted": accepted,
    }


def _scan_predecessors(
    goal, variables, domains, current, trace, attempts, cap, deadline_monotonic=None,
    *, capture_invalid=False,
):
    starting_attempts = attempts
    eligible = [name for name in variables if domains[name].index(current[name]) > 0]
    for index, name in enumerate(eligible):
        if _deadline_reached(deadline_monotonic):
            return _scan_interrupted(
                trace, current, attempts, starting_attempts, "deadline-exhausted"
            )
        attempt = _reduction_attempt(
            goal, variables, domains, current, name,
            capture_invalid=capture_invalid,
        )
        trace.append(attempt)
        attempts += 1
        if attempt["result"] == "invalid-input":
            return current, attempts - starting_attempts, False, True, "invalid-input"
        if attempt["measureAfter"] >= attempt["measureBefore"]:
            raise AssertionError("declared predecessor failed to decrease rank sum")
        if attempt["accepted"]:
            return _accepted_reduction(
                attempt, attempts, starting_attempts, cap, trace, deadline_monotonic
            )
        if attempts == cap and index + 1 < len(eligible):
            return _scan_interrupted(
                trace, current, attempts, starting_attempts, "reduction-cap",
                status="budget-exhausted",
            )
    return current, attempts - starting_attempts, False, False, None


def _minimization_context(goal, candidate_lists, assignment):
    variables, _premises, _conclusion = _goal_shape(goal)
    goal_snapshot, goal_digest = _goal_identity(goal)
    _domains_list, declared, _family_size = _candidate_family(variables, candidate_lists)
    domains = {
        name: [_canonical(_literal(value)) for value in declared[name]]
        for name in variables
    }
    initial = _canonical_assignment(variables, assignment, domains)
    return variables, goal_snapshot, goal_digest, declared, domains, initial


def minimize_counterexample(
    goal: Any,
    candidate_lists: Any,
    assignment: Any,
    *,
    max_reductions: int = 32,
    deadline_monotonic: float | None = None,
    capture_invalid: bool = False,
) -> dict:
    """Minimize a counterexample under declared immediate predecessors only.

    Variables are scanned in goal order. A predecessor replaces one value by
    the immediately preceding value in that variable's declared ordered list.
    An accepted reduction restarts the scan. The rank sum strictly decreases
    on every attempt, and irreducibility is claimed only after a complete scan
    accepts no reduction.

    capture_invalid retains the last checked witness and attempted predecessor
    on undefined arithmetic, without a minimality claim. It defaults to false.
    """
    if type(capture_invalid) is not bool:
        _fail("capture_invalid must be a boolean")
    if type(max_reductions) is not int or not 1 <= max_reductions <= 32:
        _fail("reduction cap must be an integer from 1 through 32")
    deadline_monotonic = _validated_deadline(deadline_monotonic)
    variables, goal_snapshot, goal_digest, declared, domains, initial = (
        _minimization_context(goal, candidate_lists, assignment)
    )
    if _deadline_reached(deadline_monotonic):
        return _minimization_result(
            goal_snapshot, goal_digest, declared, initial, None, [], 0,
            status="deadline-exhausted", minimality=False, assignment_checked=False,
        )
    initial_result = _check_initial_minimization(
        goal_snapshot, goal_digest, declared, initial, capture_invalid
    )
    if initial_result is not None:
        return initial_result
    return _run_minimization(
        goal_snapshot, goal_digest, declared, domains, variables, initial,
        max_reductions, deadline_monotonic, capture_invalid,
    )


def _check_initial_minimization(goal, digest, declared, initial, capture_invalid):
    try:
        status = check_witness(goal, initial)["status"]
    except ValueError as error:
        if not capture_invalid:
            raise
        result = _minimization_result(
            goal, digest, declared, initial, None, [], 0,
            status="invalid-input", minimality=False, assignment_checked=False,
        )
        result["initialCheckAttempted"] = True
        result["initialCheckError"] = str(error)
        return result
    if status == "counterexample":
        return None
    return _fail("initial assignment must be an exact counterexample")


def _run_minimization(
    goal, digest, declared, domains, variables, initial, max_reductions,
    deadline_monotonic, capture_invalid,
):
    current = dict(initial)
    trace, reductions = [], 0
    irreducible = False
    interrupted = False
    stop_reason = None
    while not irreducible and not interrupted:
        current, used, accepted, interrupted, stop_reason = _scan_predecessors(
            goal, variables, domains, current, trace, reductions,
            max_reductions, deadline_monotonic,
            capture_invalid=capture_invalid,
        )
        reductions += used
        irreducible = not accepted and not interrupted
    status = "locally-irreducible" if irreducible else (stop_reason or "budget-exhausted")
    return _minimization_result(
        goal, digest, declared, initial, current, trace, reductions,
        status=status, minimality=irreducible, assignment_checked=True,
    )


def _minimization_result(
    goal, digest, declared, initial, current, trace, attempts, *, status, minimality,
    assignment_checked,
):
    return {
        "schema": "ladon-rational-witness-minimization-v1",
        "status": status,
        "goal": goal,
        "goalSha256": digest,
        "declaredFamily": declared,
        "initialAssignment": initial,
        "assignment": current,
        "assignmentChecked": assignment_checked,
        "reductionRelation": "replace one coordinate by its immediate predecessor in its declared ordered candidate list",
        "measure": "sum of coordinate ranks in declared ordered candidate lists",
        "minimality": minimality,
        "minimalityScope": (
            "locally irreducible under the declared immediate-predecessor relation"
            if minimality
            else None
        ),
        "attemptCount": attempts,
        "reductionCount": sum(row.get("accepted", False) for row in trace),
        "trace": trace,
        "nonclaims": [
            "Minimality is scoped to the declared immediate-predecessor relation and candidate family.",
            "No global numeric minimality or source-level claim is established.",
            "A resource-exhausted result does not claim irreducibility.",
        ],
    }


def _validated_deadline(value):
    if value is None:
        return None
    if type(value) not in (int, float):
        _fail("deadline must be a finite numeric monotonic timestamp")
    try:
        normalized = float(value)
    except OverflowError:
        _fail("deadline must be a finite numeric monotonic timestamp")
    if not math.isfinite(normalized):
        _fail("deadline must be a finite numeric monotonic timestamp")
    return normalized


def _session_minimization(search, goal, candidate_lists, max_reductions, deadline):
    if search["status"] != "abstract-countermodel":
        return None
    initial = next(row["assignment"] for row in search["trace"] if row["status"] == "counterexample")
    if _deadline_reached(deadline):
        result = _minimization_result(
            search["goal"], search["goalSha256"], search["declaredFamily"],
            initial, initial, [], 0, status="deadline-exhausted-before-start",
            minimality=False, assignment_checked=False,
        )
        result["checkedAssignmentRef"] = {
            "candidateSearchTraceIndex": len(search["trace"]) - 1
        }
        return result
    return minimize_counterexample(
        search["goal"], search["declaredFamily"], initial,
        max_reductions=max_reductions,
        deadline_monotonic=deadline,
    )


def run_rational_witness_session(
    goal: Any,
    candidate_lists: Any,
    *,
    deadline_monotonic: float,
    max_candidates: int = 256,
    max_reductions: int = 32,
) -> dict:
    """Run one bounded candidate search and optional minimization on one deadline."""
    if deadline_monotonic is None:
        _fail("session deadline must be a finite numeric monotonic timestamp")
    deadline = _validated_deadline(deadline_monotonic)
    if type(max_candidates) is not int or not 1 <= max_candidates <= 256:
        _fail("candidate search cap must be an integer from 1 through 256")
    if type(max_reductions) is not int or not 1 <= max_reductions <= 32:
        _fail("reduction cap must be an integer from 1 through 32")
    search = search_candidates(
        goal, candidate_lists, max_candidates=max_candidates,
        deadline_monotonic=deadline,
    )
    minimization = _session_minimization(
        search, goal, candidate_lists, max_reductions, deadline
    )
    return {
        "schema": "ladon-rational-witness-session-v1",
        "status": search["status"],
        "roundCount": 1 if search["attemptedCount"] else 0,
        "roundLimit": 1,
        "roundsSupported": False,
        "deadlineMonotonic": deadline,
        "candidateChecks": search["attemptedCount"],
        "reductionAttempts": minimization["attemptCount"] if minimization else 0,
        "candidateSearch": search,
        "minimization": minimization,
    }
