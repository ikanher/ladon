"""Plans for live Expr-derived predicate admission; no semantic contract activation."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_admission import _NAME, FAMILY_SOURCE, _digest
from ladon.real_bound_shape import observe_bound_shape

BINDING_SOURCE = Path(__file__).parent / "lean/LadonRealBoundBinding.lean"


def _validate_measure_name(name):
    if type(name) is not str or len(name) > 256 or not _NAME.fullmatch(name):
        raise ValueError("measure must name a bounded declaration")


def _measure_arguments(observation, measure):
    closed(measure, {"declaration", "arguments"}, "bound measure")
    _validate_measure_name(measure["declaration"])
    arguments = measure["arguments"]
    binders = [row["binderId"] for row in observation["candidate"]["telescope"]]
    if (type(arguments) is not list or len(arguments) > 64
            or any(type(arg) is not str or arg not in binders for arg in arguments)):
        raise ValueError("measure arguments must name observed telescope binders")
    return [binders.index(arg) for arg in arguments]


def _alpha_expression(value):
    """Binder display names are not identity; indices, levels and instances are."""
    if isinstance(value, list):
        return [_alpha_expression(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: _alpha_expression(child) for key, child in value.items()}
    for kind in ("forallE", "lam", "letE"):
        if kind in result:
            result[kind]["name"] = "_"
    return result


def plan_bound_prefix(observation, measure):
    """Describe one exact live admission goal; freshness is checked at execution."""
    if observation.get("status") != "observed" or observation.get("candidate") is None:
        raise ValueError("a supported observed candidate is required")
    snapshot = observation["statementSnapshot"]
    actual = observe_bound_shape(snapshot["observation"]["normalizedTypeExpr"])
    if actual["candidate"] is None or actual["candidate"] != observation["candidate"]:
        raise ValueError("bound candidate differs from supported expression shape")
    indices = _measure_arguments(observation, measure)
    declaration = snapshot["selection"]["declaration"]
    expected = json.dumps(_alpha_expression(snapshot["observation"]["normalizedTypeExpr"]), ensure_ascii=False,
                          separators=(",", ":"))
    # JSON string literals are also Lean string literals; non-ASCII is retained.
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    goal = (f"ladon_bound_admission% {quote(declaration)} {quote(expected)} "
            f"{quote(measure['declaration'])} [{', '.join(map(str, indices))}]")
    result = {"schema": "ladon-bound-prefix-plan-v1", "status": "planned",
              "admission": "unresolved", "contract": None,
              "observation": deepcopy(observation), "measure": deepcopy(measure),
              "familySourceDigest": "sha256:" + hashlib.sha256(FAMILY_SOURCE.read_bytes()).hexdigest(),
              "bindingSourceDigest": "sha256:" + hashlib.sha256(BINDING_SOURCE.read_bytes()).hexdigest(),
              "goals": [{"id": "predicate-admission", "proposition": goal, "goalDigest": _digest(goal)}],
              "limitations": ["plan-is-not-checked-admission", "proof-valued-parameters-unsupported",
                              "no-scalar-composition-or-paper-norm-interpretation"]}
    result["planId"] = snapshot_identity(result)
    return result
