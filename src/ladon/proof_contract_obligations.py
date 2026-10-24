"""Bounded, conditional backward sufficient-precondition templates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ladon._contract_propagation_budget import OutputBudget
from ladon._contract_propagation_input_budget import input_bytes_exceeded
from ladon.proof_contracts import validate_contract

from ._proof_contract_obligations_result import (
    _base_result,
    _digest,
    _finish,
    _make_branch,
)
from ._proof_contract_obligations_rules import (
    _branch_specs,
    _dispatch_residual,
    _preflight_rule_values,
)
from ._proof_contract_obligations_validation import (
    _MAX_REFS,
    _closed_mapping,
    _count_refs,
    _deadline_expired,
    _read_bounds,
    _validate_interface,
    _validate_interfaces,
    _validate_rule_evidence,
)


@dataclass(frozen=True)
class BackwardTransformRequest:
    desired_contract: Any
    rule_evidence: Any
    premise_interfaces: Any
    output_interface: Any
    parameters: Any = None
    choices: Any = None
    bounds: Any = None


def _request_mapping(request):
    if not isinstance(request, BackwardTransformRequest):
        raise TypeError("request must be BackwardTransformRequest")
    return {
        "desiredContract": request.desired_contract,
        "ruleEvidence": request.rule_evidence,
        "premiseInterfaces": request.premise_interfaces,
        "outputInterface": request.output_interface,
        "parameters": request.parameters,
        "choices": request.choices,
        "bounds": request.bounds,
    }


def transform_backward_sufficient(
    request: BackwardTransformRequest, *, _deadline_observation=None
) -> dict[str, Any]:
    """Return bounded sufficient requirements or an explicit residual."""
    prepared = _validate_request(request)
    raw, caps, deadline, desired, evidence, premises, output, parameters, choices = prepared
    result = _base_result(desired, evidence)
    result["requestDigest"] = _digest(raw)
    residual = _dispatch_residual(desired, evidence, premises, output, parameters, choices)
    if residual is not None:
        return _residual_result(result, residual, caps["maxOutputBytes"])
    specs = _branch_specs(evidence["ruleId"], desired, premises, output, parameters, choices)
    if isinstance(specs, dict):
        return _residual_result(result, specs, caps["maxOutputBytes"])
    return _generate(result, specs, caps, deadline, _deadline_observation)


def _validate_request(request):
    raw = _request_mapping(request)
    if input_bytes_exceeded(raw) is not None:
        raise ValueError("aggregate input exceeds 8 MiB")
    caps, deadline = _read_bounds(request.bounds)
    evidence = _validate_rule_evidence(request.rule_evidence)
    premises = _validate_interfaces(request.premise_interfaces, caps["maxPremiseOccurrences"])
    output = _validate_interface(request.output_interface)
    parameters = _closed_mapping(request.parameters, "parameters")
    choices = _closed_mapping(request.choices, "choices")
    if _count_refs(raw) > _MAX_REFS:
        raise ValueError("opaque reference arrays exceed 256 entries")
    _preflight_rule_values(evidence, parameters, choices)
    desired = validate_contract(request.desired_contract)
    return raw, caps, deadline, desired, evidence, premises, output, parameters, choices


def _residual_result(result, residual, max_output):
    result["status"] = "residual"
    result["residuals"] = [residual]
    return _finish(result, max_output)


def _generate(result, specs, caps, deadline, deadline_observation=None):
    max_output = caps["maxOutputBytes"]
    budget = OutputBudget(max_output)
    if not budget.reserve(result, overhead=512):
        return _budget_result(result, caps, len(specs), "output-size-cap", max_output)
    branches, pending, expired = _collect_branches(
        specs, caps, deadline, budget, deadline_observation
    )
    result["branches"] = branches
    result["coverage"] = {
        "branchLimit": caps["maxBranches"],
        "pendingSplitCount": pending,
    }
    if pending:
        code = "deadline" if expired else (
            "output-size-cap" if budget.exhausted else "branch-budget"
        )
        return _budget_finish(result, pending, code, max_output)
    result["status"] = "generated"
    return _finish(result, max_output)


def _collect_branches(specs, caps, deadline, budget, deadline_observation=None):
    branches, pending = [], len(specs)
    expired = False
    for spec in specs:
        if _deadline_expired(deadline, deadline_observation):
            expired = True
            break
        if len(branches) >= caps["maxBranches"]:
            break
        if not _reserve_spec(spec, budget):
            break
        branches.append(_make_branch(spec))
        pending -= 1
    return branches, pending, expired


def _reserve_spec(spec, budget):
    occurrences = len(spec["premises"])
    if not budget.reserve(spec["desired"], copies=occurrences, overhead=1536 * occurrences + 512):
        return False
    return all(budget.reserve(row, overhead=128) for row in spec["premises"])


def _budget_result(result, caps, pending, code, max_output):
    result["status"] = "budget-exhausted"
    result["coverage"] = {"branchLimit": caps["maxBranches"], "pendingSplitCount": pending}
    return _budget_finish(result, pending, code, max_output)


def _budget_finish(result, pending, code, max_output):
    result["status"] = "budget-exhausted"
    result["residuals"] = [{"code": code, "pendingCount": pending}]
    return _finish(result, max_output)
