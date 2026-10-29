"""Closed plans for prefix-family obligations; plans confer no admission authority."""

import hashlib
import re
from copy import deepcopy
from pathlib import Path

from ladon.proof_contract_payloads import closed
from ladon.proofir_v3 import canonical_bytes

_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_NAMES = ("predicate", "measure", "objectType", "parameterType", "pointType")
FAMILY_SOURCE = Path(__file__).parent / "lean" / "LadonRealBound.lean"


def _digest(value):
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def _validate_request(request):
    closed(request, {"source", "environmentRef", *_NAMES}, "prefix admission request")
    for field in _NAMES:
        name = request[field]
        if type(name) is not str or len(name) > 256 or not _NAME.fullmatch(name):
            raise ValueError(f"{field} must be a bounded qualified declaration name")
    _validate_source(request["source"])
    _validate_environment(request["environmentRef"])


def _validate_source(source):
    closed(source, {"path", "sha256"}, "source")
    path = source["path"]
    if (type(path) is not str or len(path) > 512 or "\\" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))):
        raise ValueError("source path must be a bounded canonical relative path")
    if type(source["sha256"]) is not str or not _HASH.fullmatch(source["sha256"]):
        raise ValueError("source identity must be a SHA-256 digest")


def _validate_environment(environment):
    if (type(environment) is not str or not environment.startswith("sha256:")
            or not _HASH.fullmatch(environment[7:])):
        raise ValueError("environmentRef must be a SHA-256 identity")


def plan_prefix_admission(request):
    """Build exact goals; callers must separately verify source and every proof."""
    _validate_request(request)
    owned = deepcopy(request)
    names = {key: "_root_." + owned[key] for key in _NAMES}
    family = "_root_.Ladon.RealBound."
    types = f"(F := {names['objectType']}) (P := {names['parameterType']})"
    predicate = f"({names['predicate']})"
    propositions = (
        ("predicate-equivalence", (f"{family}Equivalent {types} (Y := {names['pointType']}) "
         f"{predicate} ({names['measure']})")),
        ("order-prefix", f"{family}OrderPrefix {types} {predicate}"),
        ("bound-monotonicity", f"{family}BoundMonotone {types} {predicate}"),
    )
    result = {
        "schema": "ladon-prefix-admission-plan-v1", "status": "planned",
        "request": owned, "admission": "unresolved", "contract": None,
        "requiredImport": "LadonRealBound", "familySourceDigest": "sha256:" +
        hashlib.sha256(FAMILY_SOURCE.read_bytes()).hexdigest(),
        "goals": [{"id": name, "proposition": proposition,
                   "goalDigest": _digest(proposition)} for name, proposition in propositions],
        "limitations": ["plan-is-not-checked-admission", "source-application-binding-unchecked",
                        "no-composition-rule", "no-derivative-or-paper-norm-interpretation"],
    }
    result["planId"] = _digest(result)
    return result
