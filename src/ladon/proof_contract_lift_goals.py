"""Planning-only source-to-formal goals for the bounded Nat/rational profile.

Generated propositions require a separate supervised Lean check. This module
does not read source files or accept checker receipts.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from fractions import Fraction

from ladon.proof_contract_refinement import _bounded_json, _validate_abstract_witness
from ladon.rational_witness import check_witness, validate_goal

_SCHEMA = "ladon-proof-contract-nat-rational-lift-plan-v1"
_IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*\Z", re.ASCII)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_MODES = {"realization", "incompatibility"}
_COMPARE = {"le": "≤", "lt": "<", "eq": "=", "ne": "≠", "ge": "≥", "gt": ">"}
_MAX_PLAN_BYTES = 1024 * 1024
_MAX_GOAL_BYTES = 256 * 1024


def plan_nat_rational_lift(goal, witness, interpretation, *, mode):
    """Validate inputs and build deterministic, explicitly unchecked goals."""
    original = _owned_inputs(goal, witness, interpretation, mode)
    goal_copy, witness_copy, interpretation_copy = original
    validate_goal(goal_copy)
    checked = check_witness(goal_copy, witness_copy["assignment"])
    if checked["status"] != "counterexample":
        raise ValueError("abstract witness assignment must refute the goal under all premises")
    variables = goal_copy["variables"]
    if (interpretation_copy["profile"] != "nat-cast-v1" or len(variables) != 1
            or _has_division(goal_copy)):
        return _unsupported(goal_copy, witness_copy, interpretation_copy, mode)
    pieces = _components(goal_copy, witness_copy, interpretation_copy, mode)
    combined = _conjoin(pieces)
    if len(combined.encode("utf-8")) > _MAX_GOAL_BYTES:
        raise ValueError("generated lift goal exceeds 256 KiB")
    record = _plan_record(goal_copy, witness_copy, interpretation_copy, mode, pieces, combined)
    if len(_canonical_json(record).encode("utf-8")) > _MAX_PLAN_BYTES:
        raise ValueError("lift plan exceeds 1 MiB")
    return {"planId": _identity(record), **record}


def _owned_inputs(goal, witness, interpretation, mode):
    if type(mode) is not str or mode not in _MODES:
        raise ValueError("mode must be realization or incompatibility")
    owned = _bounded_json({"goal": goal, "witness": witness,
                           "interpretation": interpretation, "mode": mode}, "lift request")
    _closed(owned["interpretation"], {"profile", "source", "formalClaim", "formalPredicate"}, "interpretation")
    _closed(owned["interpretation"]["source"], {"path", "sha256"}, "source reference")
    _validate_source(owned["interpretation"]["source"])
    _validate_name(owned["interpretation"]["formalClaim"], "formalClaim")
    _validate_name(owned["interpretation"]["formalPredicate"], "formalPredicate")
    _validate_profile(owned["interpretation"]["profile"])
    _validate_abstract_witness(owned["witness"])
    return owned["goal"], owned["witness"], owned["interpretation"]


def _closed(value, keys, label):
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{label} requires exactly {sorted(keys)}")


def _validate_profile(value):
    if type(value) is not str or not value or len(value.encode("utf-8")) > 128:
        raise ValueError("profile must be bounded nonempty text")


def _validate_name(value, label):
    if (type(value) is not str or len(value.encode("utf-8")) > 256
            or not _IDENTIFIER.fullmatch(value)):
        raise ValueError(f"{label} must be an ordinary qualified Lean identifier")


def _validate_source(source):
    path, digest = source["path"], source["sha256"]
    if type(path) is not str or not path or "\\" in path or path.startswith("/"):
        raise ValueError("source path must be a safe relative POSIX path")
    if any(part in {"", ".", ".."} for part in path.split("/")):
        raise ValueError("source path must use canonical relative POSIX components")
    if type(digest) is not str or not _SHA256.fullmatch(digest):
        raise ValueError("source sha256 must be 64 lowercase hexadecimal characters")


def _has_division(goal):
    return any(_expression_has_division(expression)
               for predicate in [*goal["premises"], goal["conclusion"]]
               for expression in (predicate["left"], predicate["right"]))


def _expression_has_division(expression):
    return expression.get("op") == "div" or any(
        _expression_has_division(child) for child in expression.get("args", [])
    )


def _unsupported(goal, witness, interpretation, mode):
    reason = _unsupported_reason(goal, interpretation)
    record = _plan_record(goal, witness, interpretation, mode, {}, None,
                          status="unsupported", reason=reason)
    if len(_canonical_json(record).encode("utf-8")) > _MAX_PLAN_BYTES:
        raise ValueError("lift plan exceeds 1 MiB")
    return {"planId": _identity(record), **record}


def _unsupported_reason(goal, interpretation):
    if interpretation["profile"] != "nat-cast-v1":
        return "unsupported-profile"
    if len(goal["variables"]) == 0:
        return "variable-free-goal"
    if len(goal["variables"]) != 1:
        return "multiple-variables"
    if _has_division(goal):
        return "division-unsupported"
    return "unsupported-goal"


def _components(goal, witness, interpretation, mode):
    name = goal["variables"][0]
    binder = "n"
    cast = "(_root_.Rat.ofInt (_root_.Int.ofNat n))"
    predicate = _predicate(goal["conclusion"], name, cast)
    premises = [_predicate(row, name, cast) for row in goal["premises"]]
    implication = _implication(premises, predicate)
    claim = interpretation["formalClaim"]
    formal_predicate = interpretation["formalPredicate"]
    components = {
        "fullClaimMapping": f"(_root_.{claim} ↔ (∀ {binder} : _root_.Nat, _root_.{formal_predicate} {binder}))",
        "objectMapping": f"(∀ {binder} : _root_.Nat, (_root_.{formal_predicate} {binder}) ↔ {implication})",
    }
    q = _rat(Fraction(witness["assignment"][name]))
    exact_object = f"(∃ {binder} : _root_.Nat, {cast} = {q} ∧ ¬ (_root_.{formal_predicate} {binder}))"
    if mode == "realization":
        components["outcome"] = exact_object
        components["formalRefutation"] = f"¬ (_root_.{claim})"
    else:
        components["outcome"] = f"¬ (∃ {binder} : _root_.Nat, {cast} = {q})"
    return components


def _predicate(predicate, variable, cast):
    return f"({_expression(predicate['left'], variable, cast)} {_COMPARE[predicate['op']]} {_expression(predicate['right'], variable, cast)})"


def _expression(expression, variable, cast):
    if set(expression) == {"var"}:
        if expression["var"] != variable:
            raise ValueError("unknown variable in rational expression")
        return cast
    if set(expression) == {"rat"}:
        return _rat(Fraction(expression["rat"]))
    op, args = expression["op"], expression["args"]
    if op == "add":
        return f"({_expression(args[0], variable, cast)} + {_expression(args[1], variable, cast)})"
    if op == "sub":
        return f"({_expression(args[0], variable, cast)} - {_expression(args[1], variable, cast)})"
    if op == "mul":
        return f"({_expression(args[0], variable, cast)} * {_expression(args[1], variable, cast)})"
    if op == "neg":
        return f"(-{_expression(args[0], variable, cast)})"
    if op == "abs":
        return f"(abs {_expression(args[0], variable, cast)})"
    if op == "pow":
        return f"({_expression(args[0], variable, cast)} ^ {expression['exponent']})"
    raise ValueError("unsupported rational expression operator")


def _rat(value):
    rational = value if type(value) is Fraction else Fraction(value)
    numerator, denominator = rational.numerator, rational.denominator
    if denominator == 1:
        return f"({numerator} : _root_.Rat)"
    return f"(({numerator} : _root_.Rat) / ({denominator} : _root_.Rat))"


def _implication(premises, conclusion):
    if not premises:
        return conclusion
    return f"({' ∧ '.join(premises)} → {conclusion})"


def _conjoin(components):
    return "(\n  " + " ∧\n  ".join(components.values()) + "\n)"


def _plan_record(goal, witness, interpretation, mode, components, combined,
                 status="planned", reason=None):
    return {
        "schema": _SCHEMA, "status": status,
        "goalInput": copy.deepcopy(goal), "witness": copy.deepcopy(witness),
        "interpretation": copy.deepcopy(interpretation), "mode": mode,
        "components": copy.deepcopy(components), "goal": combined,
        "sourceFormulaFidelity": "unverified", "sourceVerified": False,
        "originalClaimRefuted": False,
        "liftStatus": "pending-checks" if status == "planned" else "unsupported",
        "reason": reason,
    }


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _identity(record):
    return "sha256:" + hashlib.sha256(_canonical_json(record).encode("utf-8")).hexdigest()
