"""Bounded ownership for the route-context public API.

No native validation, filesystem access, worker dispatch, Lean, or clock reset
belongs here. The supervised route worker owns all source/artifact decisions.
"""
from __future__ import annotations

import copy
import math
import re

from ladon._proof_contract_planned_source_inputs import _planned_input_size
from ladon.proof_contract_bridge_supervision import bridge_limits

MAX_BYTES = 8 * 1024**2
_MAX_TERM_BYTES = 1024**2
_PLAN_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")
_GOAL_ID = re.compile(
    r"(?:interpretation|conditional|domain|object-map|conclusion|"
    r"premise-[0-9]{1,4}|provider-[0-9]{1,4}|source-reading|"
    r"contract-transfer|endpoint-transfer)\Z"
)
_REQUEST_KEYS = {
    "repoRoot", "analysisArtifact", "context", "selectedIdentity",
    "sourceBindings", "deadlineMonotonic", "limits",
}
_BINDING_KEYS = {
    "parentSnapshot", "providerSnapshot", "parentInterpretationRef",
    "correspondenceRef",
}
_IDENTITY_KEYS = {
    "routeId", "stepRef", "witnessRef", "branchRef", "branchIndex",
    "premiseOrdinal", "forwardContractRef", "statementRef",
    "parentWitnessRef", "interfaceId",
}


def own_inputs(request, plan_id, terms, checking):
    """Preflight aggregate input before copying any caller-owned values."""
    _operation(request, plan_id, terms, checking)
    if _planned_input_size([request, plan_id, terms]) > MAX_BYTES:
        raise ValueError("aggregate route-context input exceeds 8 MiB")
    if checking:
        _validate_terms(terms)
    _validate_shape(request)
    deadline = request["deadlineMonotonic"]
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("route-context deadline must be finite")
    limits = bridge_limits(request["limits"])
    owned = copy.deepcopy(request)
    owned["limits"] = limits
    return owned, plan_id, copy.deepcopy(terms), limits


def _operation(request, plan_id, terms, checking):
    if type(checking) is not bool:
        raise ValueError("checking must be boolean")
    if not isinstance(request, dict) or set(request) != _REQUEST_KEYS:
        raise ValueError("route-context request must use the closed schema")
    if checking:
        if not isinstance(plan_id, str) or not _PLAN_ID.fullmatch(plan_id):
            raise ValueError("checking requires an exact saved route plan identity")
    elif plan_id is not None or terms is not None:
        raise ValueError("planning does not accept a checkpoint or terms")


def _validate_shape(request):
    from ._proof_contract_obligation_check_inputs import _validate_context

    if not isinstance(request["repoRoot"], str) or not request["repoRoot"]:
        raise ValueError("repoRoot must be nonempty text")
    if not isinstance(request["analysisArtifact"], dict):
        raise TypeError("analysisArtifact must be one native envelope object")
    _validate_context(request["context"])
    identity = request["selectedIdentity"]
    if not isinstance(identity, dict) or set(identity) != _IDENTITY_KEYS:
        raise ValueError("selectedIdentity must use the exact native route occurrence schema")
    _bindings(request["sourceBindings"])


def _bindings(bindings):
    if not isinstance(bindings, dict) or set(bindings) != _BINDING_KEYS:
        raise ValueError("sourceBindings must use the closed owner schema")
    for key in ("parentSnapshot", "providerSnapshot"):
        if not isinstance(bindings[key], dict):
            raise TypeError("source snapshots must be native envelope objects")
    _reference(bindings["parentInterpretationRef"], "interpretation")
    _reference(bindings["correspondenceRef"], "correspondence")


def _reference(value, kind):
    if (not isinstance(value, dict)
            or set(value) != {"artifactRef", "kind", "localId"}
            or value["kind"] != kind
            or not isinstance(value["artifactRef"], str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", value["artifactRef"])
            or not isinstance(value["localId"], str)
            or not 1 <= len(value["localId"]) <= 512):
        raise ValueError("source binding requires an exact typed native reference")


def _validate_terms(terms):
    if not isinstance(terms, dict) or len(terms) > 4096:
        raise ValueError("terms must be a bounded route-goal mapping")
    for identity, term in terms.items():
        if (not isinstance(identity, str) or not _GOAL_ID.fullmatch(identity)
                or not isinstance(term, str) or not term.strip()
                or len(term.encode("utf-8")) > _MAX_TERM_BYTES):
            raise ValueError("invalid route goal identity or bounded proof term")


def compose_requirement(goals):
    """Compose only independently accepted reading and implication terms."""
    if not isinstance(goals, list):
        return None
    indexed = {row.get("id"): row for row in goals if isinstance(row, dict)}
    reading, transfer, requirement = [indexed.get(key) for key in
        ("source-reading", "contract-transfer", "source-requirement")]
    if not all(isinstance(row, dict) for row in (reading, transfer, requirement)):
        return None
    if not _accepted_term(reading) or not _accepted_term(transfer):
        return None
    if not _linked_formulas(reading, transfer, requirement):
        return None
    source, required = reading["goal"], requirement["goal"]
    term = (f"((show (({source}) → ({required})) from ({transfer['term']})) "
            f"(show ({source}) from ({reading['term']})))")
    return {"goalId": "source-requirement", "goal": required, "term": term}


def _accepted_term(row):
    from .proof_contract_bridge import _accepted_check

    return (row.get("status") == "checked-support" and _accepted_check(row.get("result"))
            and isinstance(row.get("term"), str) and bool(row["term"].strip()))


def _linked_formulas(reading, transfer, requirement):
    source, required = reading.get("goal"), requirement.get("goal")
    if not all(isinstance(text, str) and text.strip() for text in (source, required)):
        return False
    return (transfer.get("antecedentGoal") == source
            and transfer.get("consequentGoal") == required
            and transfer.get("goal") == f"({source}) → ({required})")
