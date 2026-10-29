"""Closed plans for a fixed joint real Frechet derivative-prefix adapter."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_admission import FAMILY_SOURCE, _digest
from ladon.real_bound_binding import BINDING_SOURCE, _alpha_expression
from ladon.real_bound_shape import observe_bound_shape

DERIVATIVE_SOURCE = Path(__file__).parent / "lean/LadonRealBoundDerivative.lean"
PROFILE = {
    "profileId": "joint-real-frechet-prefix-v1",
    "scalar": "Real",
    "measure": "norm of iteratedFDeriv Real j f (p,y), f:P*Y->Z",
    "normCarrier": "full continuous multilinear map on P*Y with codomain Z",
    "quantifiers": ["all j<=n", "all p in S", "all y:Y"],
    "instances": "source-owned local context and pinned compiled imports",
}


def plan_derivative_prefix(observation):
    """Plan exact derivative admission; neither syntax nor this plan proves it."""
    if observation.get("status") != "observed" or observation.get("candidate") is None:
        raise ValueError("a supported observed candidate is required")
    snapshot = observation["statementSnapshot"]
    actual = observe_bound_shape(snapshot["observation"]["normalizedTypeExpr"])
    if actual["candidate"] is None or actual["candidate"] != observation["candidate"]:
        raise ValueError("derivative candidate differs from supported expression shape")
    expected = json.dumps(_alpha_expression(snapshot["observation"]["normalizedTypeExpr"]),
                          ensure_ascii=False, separators=(",", ":"))
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    goal = (f"ladon_derivative_admission% {quote(snapshot['selection']['declaration'])} "
            f"{quote(expected)}")
    result = {
        "schema": "ladon-derivative-prefix-plan-v1", "status": "planned",
        "admission": "unresolved", "contract": None, "paperNormBridge": "unresolved",
        "observation": deepcopy(observation), "derivativeProfile": deepcopy(PROFILE),
        "familySourceDigest": "sha256:" + hashlib.sha256(FAMILY_SOURCE.read_bytes()).hexdigest(),
        "bindingSourceDigest": "sha256:" + hashlib.sha256(BINDING_SOURCE.read_bytes()).hexdigest(),
        "derivativeSourceDigest": "sha256:" + hashlib.sha256(DERIVATIVE_SOURCE.read_bytes()).hexdigest(),
        "goals": [{"id": "predicate-admission", "proposition": goal, "goalDigest": _digest(goal)}],
        "limitations": ["plan-is-not-checked-admission", "proof-valued-parameters-unsupported",
                        "no-paper-norm-or-regularity-interpretation", "no-native-contract-activation"],
    }
    result["planId"] = snapshot_identity(result)
    return result
