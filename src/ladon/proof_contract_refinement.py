"""Conservative result projection for abstract-witness lift attempts.

This module does not construct realizations or prove incompatibility. In
particular, an incomplete realization search cannot establish spuriousness.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path

from ladon.investigation import SourceReader

_REASONS = {
    "deadline-exhausted",
    "candidate-limit",
    "reduction-limit",
    "round-limit",
    "unsupported-realization",
}
_MAX_RECORD_BYTES = 1024 * 1024
_BRANCH_SCHEMA = "ladon-proof-contract-refinement-branch-v1"
_SOURCE_NONCLAIM = "Span validation does not certify formula fidelity."
_BRANCH_NONCLAIMS = [
    "A source citation does not certify that its expression faithfully formalizes the passage.",
    "A proposed repair is not evidence for the original claim.",
    "A refinement branch does not erase or resolve its parent discrepancy.",
]


def _closed(value, keys, label):
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{label} requires exactly {sorted(keys)}")


def _validate_json(value, label, depth=0, nodes=None):
    if nodes is None:
        nodes = [0]
    _validate_json_node(value, label, depth, nodes)


def _validate_json_node(value, label, depth, nodes):
    nodes[0] += 1
    if nodes[0] > 16384 or depth > 32:
        raise ValueError(f"{label} must be bounded JSON-native data")
    if value is None or type(value) in (bool, int, str):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{label} must contain finite JSON-native numbers")
        return
    if type(value) is list:
        for item in value:
            _validate_json_node(item, label, depth + 1, nodes)
        return
    if type(value) is dict:
        _validate_json_mapping(value, label, depth, nodes)
        return
    raise ValueError(f"{label} must contain only JSON-native values")


def _validate_json_mapping(value, label, depth, nodes):
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError(f"{label} must use JSON-native string keys")
        _validate_json_node(item, label, depth + 1, nodes)


def _bounded_json(value, label):
    _validate_json(value, label)
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError(f"{label} must be bounded JSON data") from error
    if len(encoded.encode("utf-8")) > _MAX_RECORD_BYTES:
        raise ValueError(f"{label} exceeds 1 MiB")
    return json.loads(encoded)


def _validate_abstract_witness(value):
    _closed(value, {"id", "status", "assignment"}, "abstract witness")
    if (not isinstance(value["id"], str) or not value["id"]
            or len(value["id"].encode("utf-8")) > 128):
        raise ValueError("abstract witness ID must be bounded nonempty text")
    if value["status"] != "abstract-countermodel":
        raise ValueError("lift classification requires an abstract countermodel")
    if not isinstance(value["assignment"], dict) or len(value["assignment"]) > 32:
        raise ValueError("abstract witness assignment must be a bounded object")
    return _bounded_json(value, "abstract witness")


def _validate_lift_attempt(value):
    if not isinstance(value, dict):
        raise TypeError("lift attempt must be an object")
    if value.get("status") != "search-incomplete":
        raise ValueError("unsupported lift result")
    _closed(value, {"status", "reason", "evidence"}, "lift attempt")
    if not isinstance(value["reason"], str) or value["reason"] not in _REASONS:
        raise ValueError("unsupported lift attempt reason")
    evidence = value["evidence"]
    if (not isinstance(evidence, str) or not evidence.strip()
            or len(evidence.encode("utf-8")) > 4096):
        raise ValueError("lift attempt evidence must be bounded nonempty text")
    return _bounded_json(value, "lift attempt")


def classify_lift_result(abstract_witness, lift_attempt):
    """Keep an incomplete lift unresolved while preserving its input evidence.

    This intentionally accepts no purported realization or incompatibility
    result: those outcomes need checked evidence that this module does not yet
    produce or validate.
    """
    witness = _validate_abstract_witness(abstract_witness)
    attempt = _validate_lift_attempt(lift_attempt)
    return {
        "witnessId": witness["id"],
        "abstractWitness": copy.deepcopy(witness),
        "liftAttempt": copy.deepcopy(attempt),
        "status": "unsupported",
        "originalClaimRefuted": False,
        "spuriousnessEvidence": None,
        "openObligation": "checked-realization-or-incompatibility",
    }


def _canonical_json(value, label):
    normalized = _bounded_json(value, label)
    encoded = json.dumps(
        normalized, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    return normalized, encoded


def _refinement_digest(record):
    payload = {key: value for key, value in record.items() if key != "id"}
    _normalized, encoded = _canonical_json(payload, "refinement branch")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _content_identity(value):
    _normalized, encoded = _canonical_json(value, "immutable finding")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _text(value, label, limit=4096):
    if type(value) is not str or not value.strip() or len(value.encode("utf-8")) > limit:
        raise ValueError(f"{label} must be bounded nonempty text")


def _finding(value):
    _closed(value, {"id", "status", "discrepancy", "witness"}, "original finding")
    _text(value["id"], "finding ID", 128)
    if value["status"] != "abstract-countermodel":
        raise ValueError("refinement requires an abstract-countermodel finding")
    if not isinstance(value["discrepancy"], dict) or not isinstance(value["witness"], dict):
        raise TypeError("finding must preserve a discrepancy and witness object")
    normalized, _encoded = _canonical_json(value, "original finding")
    return normalized


def _branch_original(value):
    required = {
        "id", "schema", "branchKind", "parentId", "originalFinding", "discrepancy",
        "witness", "constraints", "onlyNewConstraints", "nonclaims",
    }
    _closed(value, required, "parent refinement branch")
    if value["schema"] != _BRANCH_SCHEMA or value["id"] != _refinement_digest(value):
        raise ValueError("parent refinement branch identity is invalid")
    _text(value["parentId"], "parent identity", 128)
    original = _finding(value["originalFinding"])
    if value["discrepancy"] != original["discrepancy"] or value["witness"] != original["witness"]:
        raise ValueError("parent refinement branch changed its original evidence")
    return original


def _validate_constraint_list(constraints, source_reader):
    if type(constraints) is not list or len(constraints) > 64:
        raise ValueError("parent refinement constraints must be a bounded list")
    for constraint in constraints:
        _validate_constraint(constraint, source_reader)


def _validate_branch_metadata(value, constraints):
    ids = [item["id"] for item in constraints]
    if len(ids) != len(set(ids)):
        raise ValueError("parent refinement constraint IDs must be unique")
    if value["branchKind"] != _branch_kind(constraints):
        raise ValueError("parent refinement branch kind does not match its constraints")
    if value["nonclaims"] != _BRANCH_NONCLAIMS:
        raise ValueError("parent refinement branch nonclaims were altered")
    additions = value["onlyNewConstraints"]
    if type(additions) is not list or not additions:
        raise ValueError("parent refinement must retain its nonempty additions")
    if constraints[-len(additions):] != additions:
        raise ValueError("parent refinement additions do not match cumulative constraints")


def _branch_constraints(value, source_reader):
    constraints = value["constraints"]
    _validate_constraint_list(constraints, source_reader)
    _validate_branch_metadata(value, constraints)


def _verify_branch(value, source_reader):
    _branch_original(value)
    _branch_constraints(value, source_reader)
    normalized, _encoded = _canonical_json(value, "parent refinement branch")
    return normalized


def _validate_source_justification(value, source_reader):
    _closed(value, {"kind", "source", "nonclaim"}, "source justification")
    if value["kind"] != "source-cited-refinement" or value["nonclaim"] != _SOURCE_NONCLAIM:
        raise ValueError("source justification must preserve the fixed fidelity limitation")
    source = value["source"]
    _closed(source, {"path", "startLine", "endLine", "quote", "sha256"}, "source reference")
    source_reader.span(source, "quote")


def _validate_repair_justification(value):
    _closed(value, {"kind", "rationale"}, "repair justification")
    if value["kind"] != "proposed-repair":
        raise ValueError("unsupported refinement justification")
    _text(value["rationale"], "repair rationale")


def _validate_constraint(value, source_reader):
    _closed(value, {"id", "expression", "justification"}, "added constraint")
    _text(value["id"], "constraint ID", 128)
    _canonical_json(value["expression"], "constraint expression")
    justification = value["justification"]
    if not isinstance(justification, dict):
        raise TypeError("constraint justification must be an object")
    if justification.get("kind") == "source-cited-refinement":
        _validate_source_justification(justification, source_reader)
    elif justification.get("kind") == "proposed-repair":
        _validate_repair_justification(justification)
    else:
        raise ValueError("unsupported constraint justification")
    _canonical_json(value, "added constraint")


def _parent_state(parent, source_reader):
    if isinstance(parent, dict) and parent.get("schema") == _BRANCH_SCHEMA:
        branch = _verify_branch(parent, source_reader)
        return (branch["id"], branch["originalFinding"],
                copy.deepcopy(branch["constraints"]))
    finding = _finding(parent)
    return _content_identity(finding), finding, []


def _branch_kind(constraints):
    kinds = {item["justification"]["kind"] for item in constraints}
    if kinds == {"proposed-repair"}:
        return "proposed-repair"
    if kinds == {"source-cited-refinement"}:
        return "source-cited-refinement"
    return "mixed-refinement-and-repair"


def _new_constraints(constraints, source_reader):
    if type(constraints) is not list or not constraints or len(constraints) > 64:
        raise ValueError("new constraints must be a nonempty bounded list")
    for item in constraints:
        _validate_constraint(item, source_reader)
    additions = [_canonical_json(item, "added constraint")[0] for item in constraints]
    kinds = {item["justification"]["kind"] for item in additions}
    if len(kinds) != 1:
        raise ValueError("one branch cannot mix source refinement and proposed repair")
    return additions


def _cumulative_constraints(inherited, additions):
    cumulative = inherited + additions
    if len(cumulative) > 64:
        raise ValueError("refinement branch exceeds 64 cumulative constraints")
    ids = [item["id"] for item in cumulative]
    if len(ids) != len(set(ids)):
        raise ValueError("refinement constraint IDs must be unique across the branch")
    return cumulative


def create_refinement_branch(parent, constraints, *, source_root):
    """Append source-cited constraints or a separate proposed-repair branch.

    Source spans and identities are checked, but their semantic relationship to
    the supplied expression remains a nonclaim for independent interpretation.
    """
    reader = SourceReader(Path(source_root))
    parent_id, original, inherited = _parent_state(parent, reader)
    additions = _new_constraints(constraints, reader)
    cumulative = _cumulative_constraints(inherited, additions)
    record = {
        "schema": _BRANCH_SCHEMA,
        "branchKind": _branch_kind(cumulative),
        "parentId": parent_id,
        "originalFinding": copy.deepcopy(original),
        "discrepancy": copy.deepcopy(original["discrepancy"]),
        "witness": copy.deepcopy(original["witness"]),
        "constraints": cumulative,
        "onlyNewConstraints": additions,
        "nonclaims": list(_BRANCH_NONCLAIMS),
    }
    _normalized, _encoded = _canonical_json(record, "refinement branch")
    result = {"id": _refinement_digest(record), **record}
    return result


_RATIONAL_REFINEMENT_SCHEMA = "ladon-rational-refinement-check-v1"
_RATIONAL_REFINEMENT_CHECKER = {
    "name": "ladon.rational_witness.check_witness",
    "schema": "ladon-rational-witness-v1",
}


def _identity_digest(value, label):
    normalized = _bounded_json(value, label)
    encoded = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest(), encoded


def _rational_refinement_request(branch, base_goal, assignment, source_root):
    """Validate and derive the exact rational request represented by a branch.

    Semantic identities hash sorted, compact UTF-8 JSON with literal Unicode
    characters (``ensure_ascii=False``). Assignment identity preserves the
    caller's rational spelling while ignoring mapping key order.
    """
    from ladon.rational_witness import check_witness, validate_goal

    reader = SourceReader(Path(source_root))
    verified_branch = _verify_branch(branch, reader)
    normalized_base, _base_encoded = _canonical_json(base_goal, "base rational goal")
    validate_goal(normalized_base)
    normalized_assignment, _assignment_encoded = _canonical_json(
        assignment, "rational assignment"
    )

    derived_goal = copy.deepcopy(normalized_base)
    constraint_checks = []
    for constraint in verified_branch["constraints"]:
        expression, _expression_encoded = _canonical_json(
            constraint["expression"], "rational refinement predicate"
        )
        if (type(expression) is not dict
                or set(expression) != {"op", "left", "right"}):
            raise ValueError(
                "rational refinement constraints must be predicate ASTs"
            )
        constraint_checks.append({
            "constraintId": constraint["id"],
            "expressionSha256": _identity_digest(
                expression, "rational refinement predicate"
            )[0],
            "justificationKind": constraint["justification"]["kind"],
        })
        derived_goal["premises"].append(expression)

    validate_goal(derived_goal)
    witness_check = check_witness(derived_goal, normalized_assignment)
    base_goal_id, _base_encoded = _identity_digest(normalized_base, "base rational goal")
    derived_goal_id, _derived_encoded = _identity_digest(
        derived_goal, "derived rational goal"
    )
    semantic_request = {
        "schema": _RATIONAL_REFINEMENT_SCHEMA,
        "branchId": verified_branch["id"],
        "branchKind": verified_branch["branchKind"],
        "originalFindingId": verified_branch["originalFinding"]["id"],
        "baseGoalSha256": base_goal_id,
        "derivedGoalSha256": derived_goal_id,
        "assignment": normalized_assignment,
        "checkerIdentity": _RATIONAL_REFINEMENT_CHECKER,
    }
    check_id, _request_encoded = _identity_digest(
        semantic_request, "rational refinement semantic request"
    )
    result = {
        **semantic_request,
        "baseGoal": normalized_base,
        "derivedGoal": derived_goal,
        "constraintChecks": constraint_checks,
        "witnessCheck": witness_check,
        "checkId": check_id,
        "originalClaimRefuted": False,
        "sourceFormulaFidelity": "unverified",
        "nonclaims": [
            "The result applies only to the encoded rational goal and assignment.",
            "A source citation does not establish formula fidelity.",
            "A proposed repair is not evidence for the original claim.",
            "A non-counterexample does not establish universal truth.",
        ],
    }
    result_digest, _result_encoded = _identity_digest(
        result, "rational refinement result"
    )
    result["resultDigest"] = result_digest
    return result


def check_rational_refinement(branch, base_goal, assignment, *, source_root):
    """Check one assignment against branch predicates added as exact premises.

    This checks only the supplied rational AST and assignment. A source citation
    remains a citation; it is not a checked translation of manuscript prose.
    """
    return _rational_refinement_request(branch, base_goal, assignment, source_root)


def verify_rational_refinement_result(
    result, branch, base_goal, assignment, *, source_root
):
    """Recompute a rational refinement check under its current exact inputs."""
    normalized_result, supplied_encoded = _canonical_json(
        result, "rational refinement result"
    )
    expected = _rational_refinement_request(
        branch, base_goal, assignment, source_root
    )
    _expected_normalized, expected_encoded = _canonical_json(
        expected, "recomputed rational refinement result"
    )
    if supplied_encoded != expected_encoded:
        raise ValueError("rational refinement result does not match current inputs")
    return normalized_result
