"""Exact source-bound predicate and scalar obligations for native Real records."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_admission import _digest
from ladon.real_bound_binding import _alpha_expression
from ladon.real_bound_binding_check import validate_binding_plan
from ladon.real_bound_native_profile import PROFILE_DIGEST

SCALAR_SOURCE = Path(__file__).parent / "lean/LadonRealBoundScalars.lean"


def plan_real_bound(binding_plan):
    """Plan both required checks; a predicate-only receipt cannot admit a record."""
    validate_binding_plan(binding_plan)
    observation = binding_plan["observation"]
    snapshot = observation["statementSnapshot"]
    binders = [row["binderId"] for row in observation["candidate"]["telescope"]]
    guard = binders.index(observation["candidate"]["guards"]["boundNonnegative"])
    expected = json.dumps(_alpha_expression(snapshot["observation"]["normalizedTypeExpr"]),
                          ensure_ascii=False, separators=(",", ":"))
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    goal = (f"ladon_scalar_admission% {quote(snapshot['selection']['declaration'])} "
            f"{quote(expected)} {guard}")
    result = {
        "schema": "ladon-real-bound-admission-plan-v1", "status": "planned",
        "admission": "unresolved", "contract": None, "profileDigest": PROFILE_DIGEST,
        "bindingPlan": deepcopy(binding_plan),
        "scalarSourceDigest": "sha256:" + hashlib.sha256(SCALAR_SOURCE.read_bytes()).hexdigest(),
        "goals": [deepcopy(binding_plan["goals"][0]),
                  {"id": "scalar-semantics", "proposition": goal, "goalDigest": _digest(goal)}],
    }
    result["planId"] = snapshot_identity(result)
    return result


def validate_real_plan(plan):
    if not isinstance(plan, dict) or plan != plan_real_bound(plan["bindingPlan"]):
        raise ValueError("stale or altered Real admission plan")
