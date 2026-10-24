"""Bounded backward route transforms and occurrence attribution."""

from __future__ import annotations

from datetime import UTC, datetime

from ladon._contract_propagation_budget import fingerprint
from ladon.proof_contract_obligations import BackwardTransformRequest, transform_backward_sufficient
from ladon.proof_contract_rules import PROFILE

from ._proof_contract_obligation_planner_validation import _refkey


def _interface_for_occurrence(occurrence, interfaces, witnesses=None):
    contract_ref = occurrence.get("contractRef", {})
    if contract_ref.get("kind") == "contract":
        for interface in interfaces:
            if interface.get("contractRef") == contract_ref:
                return _backward_interface(interface)
    if contract_ref.get("kind") == "contract-route" and witnesses:
        parent = witnesses.get(contract_ref.get("localId"))
        interface_id = parent.get("interfaceId") if parent else None
        return next(
            (
                _backward_interface(row)
                for row in interfaces
                if row.get("interfaceId") == interface_id
            ),
            None,
        )
    return None


def _backward_interface(value):
    return {
        key: ([ref["localId"] for ref in item] if key == "evidenceRefs" else item)
        for key, item in value.items()
        if key != "contractRef"
    }


def _backward_parameters(value):
    return {
        key: [row["localId"] if type(row) is dict else row for row in item]
        if key.endswith("Refs")
        else item
        for key, item in value.items()
    }


def _backward_for_route(
    path,
    desired,
    step_by_key,
    bindings,
    interfaces,
    choices,
    ledger,
    deadline,
    bounds,
    output_budget,
    *,
    bundle_mode=False,
    route_id=None,
    request_digest=None,
    deadline_observation=None,
):
    if bundle_mode:
        return _backward_for_route_bundled(
            path, desired, step_by_key, bindings, interfaces, choices, ledger, deadline,
            bounds, output_budget, route_id, request_digest,
            deadline_observation,
        )
    requirements, residuals, pending = [], [], []
    witnesses = {ref: witness for ref, witness in path}
    queue = [(path[-1][0], desired)] if path else []
    admitted = set()
    interface_by_id = {row["interfaceId"]: row for row in interfaces}
    while queue:
        witness_ref, output = queue.pop(0)
        key = (witness_ref, fingerprint(output))
        if key in admitted:
            continue
        admitted.add(key)
        found, errors, stop_reason = _backward_unit(
            witness_ref,
            output,
            witnesses,
            step_by_key,
            bindings,
            interfaces,
            choices,
            interface_by_id,
            bounds,
            ledger,
            deadline,
            output_budget,
        )
        if stop_reason:
            pending.append(
                {
                    "stepRef": stop_reason["stepRef"],
                    "branchRef": witness_ref,
                    "reason": stop_reason["reason"],
                }
            )
            pending.extend(_queued_pending(queue, witnesses, stop_reason["reason"]))
            break
        admitted_rows, stopped = found
        requirements.extend(admitted_rows)
        residuals.extend(errors)
        witness = witnesses[witness_ref]
        queue.extend(_next_backward_work(admitted_rows, witness, witnesses))
        budget_pending = _backward_budget_pending(errors, witness, witness_ref)
        if budget_pending:
            pending.append(budget_pending)
            pending.extend(_queued_pending(queue, witnesses, "backward-branch-budget"))
            break
        if stopped:
            pending.append(_output_pending(output_budget, witness["stepRef"], witness_ref))
            pending.extend(_queued_pending(queue, witnesses, "output-size-cap"))
            break
    return requirements, residuals, pending


def _backward_for_route_bundled(
    path, desired, step_by_key, bindings, interfaces, choices, ledger, deadline,
    bounds, output_budget, route_id, request_digest, deadline_observation,
):
    from ._proof_contract_obligation_bundle_walk import backward_bundle

    return backward_bundle(
        path, desired, step_by_key, bindings, interfaces, choices, ledger, deadline, bounds,
        output_budget, route_id, request_digest, deadline_observation, _backward_unit,
    )


def _backward_unit(
    witness_ref,
    output,
    witnesses,
    step_by_key,
    bindings,
    interfaces,
    choices,
    interface_by_id,
    bounds,
    ledger,
    deadline,
    output_budget,
    *, deadline_observation=None,
):
    witness = witnesses.get(witness_ref)
    if witness is None or "stepRef" not in witness:
        return ([], False), [], None
    key = _refkey(witness["stepRef"])
    step, binding = step_by_key[key], bindings.get(key)
    if binding is None:
        return ([], False), [{"code": "missing-rule-binding", "stepRef": step["stepRef"]}], None
    branch_count = _choice_count(choices.get(key, {}))
    if not output_budget.admits(output):
        return ([], False), [], {"stepRef": step["stepRef"], "reason": "output-size-cap"}
    remaining = output_budget.limit - output_budget.used
    if remaining < 1024:
        return ([], False), [], {"stepRef": step["stepRef"], "reason": "output-size-cap"}
    reason = _reserve_backward_work(
        branch_count, ledger, deadline, step["stepRef"], deadline_observation
    )
    if reason:
        return ([], False), [], {"stepRef": step["stepRef"], "reason": reason}
    found, errors, _ = _apply_backward_step(
        output,
        witness_ref,
        witness,
        step,
        binding,
        interfaces,
        witnesses,
        choices.get(key, {}),
        interface_by_id,
        {**bounds, "maxOutputBytes": remaining},
        deadline_observation=deadline_observation,
    )
    admitted, stopped = _admit_requirements(found, output_budget)
    return (admitted, stopped), errors, None


def _admit_requirements(rows, budget):
    admitted = []
    for row in rows:
        if not budget.reserve(row, copies=2, overhead=8):
            return admitted, True
        admitted.append(row)
    return admitted, False


def _backward_budget_pending(errors, witness, witness_ref):
    if not any(row.get("code") == "backward-budget-exhausted" for row in errors):
        return None
    return {
        "stepRef": witness["stepRef"],
        "branchRef": witness_ref,
        "reason": "backward-branch-budget",
    }


def _output_pending(budget, step_ref, witness_ref):
    return {"stepRef": step_ref, "branchRef": witness_ref, "reason": "output-size-cap"}


def _admit_output_or_pending(budget, value, step_ref, witness_ref):
    if budget.admits(value):
        return None
    return _output_pending(budget, step_ref, witness_ref)


def _queued_pending(queue, witnesses, reason):
    pending = []
    seen = set()
    for witness_ref, _ in queue:
        if witness_ref in seen:
            continue
        seen.add(witness_ref)
        witness = witnesses.get(witness_ref, {})
        if witness.get("stepRef"):
            pending.append(
                {"stepRef": witness["stepRef"], "branchRef": witness_ref, "reason": reason}
            )
    return pending


def _reserve_backward_work(branch_count, ledger, deadline, step_ref, observation=None):
    if observation is not None and observation.expired():
        return "deadline"
    if observation is None and deadline is not None and datetime.now(UTC) >= deadline:
        return "deadline"
    if ledger["stepsRemaining"] < 1:
        return "shared-step-budget"
    if (
        branch_count > ledger["maxCombinationsPerStep"]
        or branch_count > ledger["combinationsRemaining"]
    ):
        return "shared-combination-budget"
    ledger["stepsRemaining"] -= 1
    ledger["combinationsRemaining"] -= branch_count
    ledger["plannerSteps"] += 1
    ledger["totalSteps"] += 1
    ledger["plannerCombinations"] += branch_count
    ledger["totalCombinations"] += branch_count
    ledger["plannerStepRefs"].append(step_ref)
    return None


def _next_backward_work(requirements, witness, witnesses):
    occurrences = witness.get("premiseOccurrences", [])
    return [
        (occurrences[row["premiseOrdinal"]]["parentWitnessRef"], row["contractRecord"])
        for row in requirements
        if row["premiseOrdinal"] < len(occurrences)
        and occurrences[row["premiseOrdinal"]].get("parentWitnessRef") in witnesses
    ]


def _choice_count(choices):
    for key in ("lossSplits", "weakenLossOffsets"):
        if key in choices:
            return max(1, len(choices[key]))
    return 1


def _apply_backward_step(
    output,
    witness_ref,
    witness,
    step,
    binding,
    interfaces,
    witnesses,
    choices,
    interface_by_id,
    bounds,
    *, deadline_observation=None,
):
    out_interface = interface_by_id[binding["outputInterfaceId"]]
    premises = [
        _interface_for_occurrence(row, interfaces, witnesses)
        for row in witness.get("premiseOccurrences", [])
    ]
    if not premises:
        return [], [{"code": "missing-occurrence-interface", "stepRef": step["stepRef"]}], output
    if any(row is None for row in premises):
        return [], [{"code": "missing-occurrence-interface", "stepRef": step["stepRef"]}], output
    result = _transform_application(
        output, binding, premises, out_interface, choices, bounds,
        deadline_observation=deadline_observation,
    )
    if not _has_branches(result):
        return [], result.get("residuals", []), output
    rows = []
    for branch_index, branch in enumerate(result["branches"]):
        branch_ref = (
            "sha256:"
            + fingerprint(
                [
                    witness_ref,
                    step["stepRef"],
                    output,
                    branch_index,
                    branch["requirements"],
                ]
            ).hex()
        )
        rows.extend(
            _tag_requirement(row, witness_ref, step, witness, branch_ref, branch_index)
            for row in branch["requirements"]
        )
    first = result["branches"][0]["requirements"]
    next_output = first[0]["contractRecord"] if first else output
    return rows, _backward_result_residuals(result), next_output


def _has_branches(result):
    return result.get("status") in {"generated", "budget-exhausted"} and bool(
        result.get("branches")
    )


def _backward_result_residuals(result):
    residuals = list(result.get("residuals", []))
    if result.get("status") == "budget-exhausted":
        residuals.append(
            {
                "code": "backward-budget-exhausted",
                "pendingCount": result.get("coverage", {}).get("pendingSplitCount", 0),
            }
        )
    return residuals


def _transform_application(output, binding, premises, out_interface, choices, bounds,
                           *, deadline_observation=None):
    rule_id = binding["ruleId"]
    evidence = {
        "ruleId": rule_id,
        "ruleRef": binding["ruleRef"]["localId"],
        "ruleDeclaration": PROFILE["rules"].get(rule_id, "unsupported"),
        "profileDigest": binding["profileDigest"],
        "attributionStatus": "unverified",
        "evidenceRefs": [row["localId"] for row in binding["evidenceRefs"]],
    }
    try:
        return transform_backward_sufficient(
            BackwardTransformRequest(
                desired_contract=output,
                rule_evidence=evidence,
                premise_interfaces=premises,
                output_interface=_backward_interface(out_interface),
                parameters=_backward_parameters(binding.get("parameters", {})),
                choices=choices,
                bounds=_backward_bounds(bounds),
            ),
            _deadline_observation=deadline_observation,
        )
    except (TypeError, ValueError):
        return {
            "status": "residual",
            "residuals": [{"code": "invalid-backward-template-input"}],
            "branches": [],
        }


def _backward_bounds(bounds):
    return {
        "maxOutputBytes": bounds["maxOutputBytes"],
        "maxBranches": bounds["maxBackwardBranches"],
        **({"deadlineUtc": bounds["deadlineUtc"]} if bounds.get("deadlineUtc") else {}),
    }


def _tag_requirement(row, witness_ref, step, witness, branch_ref, branch_index):
    ordinal = row["premiseOrdinal"]
    occurrences = witness.get("premiseOccurrences", [])
    forward_ref = occurrences[ordinal].get("contractRef") if ordinal < len(occurrences) else None
    statement_ref = occurrences[ordinal].get("statementRef") if ordinal < len(occurrences) else None
    parent_witness_ref = (
        occurrences[ordinal].get("parentWitnessRef") if ordinal < len(occurrences) else None
    )
    return {
        **row,
        "stepRef": step["stepRef"],
        "witnessRef": witness_ref,
        "forwardContractRef": forward_ref,
        "branchRef": branch_ref,
        "branchIndex": branch_index,
        "statementRef": statement_ref,
        "parentWitnessRef": parent_witness_ref,
    }
