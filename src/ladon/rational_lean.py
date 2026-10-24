"""Bounded encoding of rational witness checks as closed Lean propositions."""

from __future__ import annotations

from fractions import Fraction

from ladon.rational_witness import check_witness

_SCHEMA = "ladon-rational-lean-encoding-v1"
_CHECKER = {
    "name": "ladon.rational_witness.check_witness",
    "schema": "ladon-rational-witness-v1",
}
_MAX_OUTPUT_BYTES = 4 * 1024 * 1024
_COMPARISONS = {
    "le": "≤",
    "lt": "<",
    "eq": "=",
    "ne": "≠",
    "ge": "≥",
    "gt": ">",
}
_BINARY = {"add": "+", "sub": "-", "mul": "*", "div": "/"}


def _rational_value(value):
    if type(value) is Fraction:
        return value
    if type(value) not in (int, str):
        raise ValueError("validated rational literals must be integers or strings")
    return Fraction(value)


def _lean_rational(value):
    rational = _rational_value(value)
    numerator = rational.numerator
    denominator = rational.denominator
    if denominator == 1:
        return f"({numerator} : ℚ)"
    return f"(({numerator} : ℚ) / ({denominator} : ℚ))"


def _lean_expression(expression, environment):
    keys = set(expression)
    if keys == {"var"}:
        return _lean_rational(environment[expression["var"]])
    if keys == {"rat"}:
        return _lean_rational(expression["rat"])

    operator = expression["op"]
    arguments = expression["args"]
    if operator in _BINARY:
        left = _lean_expression(arguments[0], environment)
        right = _lean_expression(arguments[1], environment)
        return f"({left} {_BINARY[operator]} {right})"
    if operator == "neg":
        return f"(-{_lean_expression(arguments[0], environment)})"
    if operator == "abs":
        return f"(abs {_lean_expression(arguments[0], environment)})"
    if operator == "pow":
        value = _lean_expression(arguments[0], environment)
        return f"({value} ^ {expression['exponent']})"
    raise ValueError("unsupported rational expression operator")


def _lean_predicate(predicate, environment):
    operator = predicate["op"]
    try:
        comparison = _COMPARISONS[operator]
    except KeyError as error:
        raise ValueError("unsupported rational predicate operator") from error
    left = _lean_expression(predicate["left"], environment)
    right = _lean_expression(predicate["right"], environment)
    return f"({left} {comparison} {right})"


def _obligation(identifier, kind, predicate, expected_holds, environment):
    rendered = _lean_predicate(predicate, environment)
    expected = "true" if expected_holds else "false"
    return {
        "id": identifier,
        "goalId": identifier,
        "kind": kind,
        "expectedHolds": expected_holds,
        "leanProposition": f"decide ({rendered}) = {expected}",
    }


def encode_rational_goal(goal, assignment):
    """Encode one exact rational witness check as closed Lean propositions.

    The rational checker validates the complete AST, assignment, arithmetic
    bounds and every evaluated expression before this function returns any
    Lean text. Returned propositions establish only individual evaluations at
    the supplied assignment; source correspondence and theorem validity remain
    unverified.
    """
    checked = check_witness(goal, assignment)
    environment = {
        name: _rational_value(assignment[name]) for name in goal["variables"]
    }
    obligations = [
        _obligation(
            f"premise-{index:04d}",
            "premise",
            predicate,
            checked["premises"][index]["holds"],
            environment,
        )
        for index, predicate in enumerate(goal["premises"])
    ]
    obligations.append(
        _obligation(
            "conclusion",
            "conclusion",
            goal["conclusion"],
            checked["conclusion"]["holds"],
            environment,
        )
    )
    lean_goal_text = "\n".join(item["leanProposition"] for item in obligations)
    if len(lean_goal_text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        raise ValueError("encoded rational Lean goals exceed 4 MiB")
    return {
        "schema": _SCHEMA,
        "status": checked["status"],
        "sourceSemanticsStatus": "unverified",
        "checkerIdentity": _CHECKER.copy(),
        "obligations": obligations,
        "leanGoalText": lean_goal_text,
        "witnessCheck": checked,
        "nonclaims": [
            "These goals check only exact rational predicates at the supplied assignment.",
            "A generated or checked proposition does not establish source formula fidelity.",
            "A finite assignment does not establish universal truth or theorem falsity.",
        ],
    }
