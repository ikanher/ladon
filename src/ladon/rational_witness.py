"""Exact, bounded rational arithmetic for checking candidate local witnesses.

A successful check is a counterexample to the encoded implication only when all
premises hold and the conclusion fails. Other outcomes make no truth claim.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Any

_SCHEMA = "ladon-rational-witness-v1"
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,31}\Z", re.ASCII)
_LITERAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?\Z", re.ASCII)
_MAX_BITS = 4096
_MAX_NODES = 4096
_MAX_DEPTH = 32


def _fail(message: str) -> None:
    raise ValueError(message)


def _literal(value: Any) -> Fraction:
    if isinstance(value, bool):
        _fail("boolean is not a rational literal")
    if isinstance(value, int):
        if value.bit_length() > 426 or len(str(value)) > 128:
            _fail("rational literal exceeds 128 characters")
        result = Fraction(value)
    elif isinstance(value, str):
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
    if not isinstance(value, dict) or set(value) != keys:
        _fail(f"{what} has invalid shape")
    return value


def _predicate_shape(value: Any) -> None:
    p = _mapping(value, {"op", "left", "right"}, "predicate")
    if not isinstance(p["op"], str) or p["op"] not in {"le", "lt", "eq", "ne", "ge", "gt"}:
        _fail("unknown predicate operator")


def _count_node(count: list[int], depth: int) -> None:
    count[0] += 1
    if count[0] > _MAX_NODES:
        _fail("goal exceeds 4096 AST nodes")
    if depth > _MAX_DEPTH:
        _fail("expression depth exceeds 32")


def _expression_shape(value: Any, names: set[str], depth: int, count: list[int]) -> None:
    _count_node(count, depth)
    if not isinstance(value, dict):
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
    if not isinstance(name, str) or not _NAME.fullmatch(name) or name not in names:
        _fail("unknown variable")


def _operator_shape(value: dict, names: set[str], depth: int, count: list[int]) -> None:
    op, args = value["op"], value["args"]
    if not isinstance(args, list):
        _fail("operator arguments must be a list")
    if not isinstance(op, str):
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
    if value["op"] != "pow" or not isinstance(value["args"], list) or len(value["args"]) != 1:
        _fail("invalid power expression")
    exponent = value["exponent"]
    if isinstance(exponent, bool) or not isinstance(exponent, int) or not 0 <= exponent <= 8:
        _fail("power exponent must be an integer from 0 through 8")
    _expression_shape(value["args"][0], names, depth + 1, count)


def _variables_shape(variables: Any) -> None:
    if not isinstance(variables, list) or len(variables) > 32:
        _fail("variables must be a list of at most 32 names")
    if any(not isinstance(n, str) or not _NAME.fullmatch(n) for n in variables):
        _fail("invalid variable name")
    if len(set(variables)) != len(variables):
        _fail("variable names must be unique")


def _goal_shape(goal: Any) -> tuple[list[str], list[Any], Any]:
    g = _mapping(goal, {"variables", "premises", "conclusion"}, "goal")
    variables, premises = g["variables"], g["premises"]
    _variables_shape(variables)
    if not isinstance(premises, list) or len(premises) > 64:
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
    if not isinstance(assignment, dict) or set(assignment) != set(variables):
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
