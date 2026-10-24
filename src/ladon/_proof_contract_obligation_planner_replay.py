"""Budgeted replay of exact native witness DAGs through registered transfers."""

from ladon._contract_propagation_budget import OutputBudget
from ladon._contract_propagation_inputs import read_contracts
from ladon._contract_propagation_transfer import _transfer
from ladon._contract_propagation_validation import _validate_inputs
from ladon._proofir_derivation_core import _Graph, _key
from ladon.proofir_v3 import validate_envelope

from ._proof_contract_obligation_planner_validation import _refkey


def replay_context(request, forward):
    derivation = validate_envelope(request.derivation_artifact).to_dict()
    graph = _Graph.build(derivation)
    contracts = read_contracts(request.contract_artifacts, derivation["environmentRef"])
    bindings, interfaces, _ = _validate_inputs(
        request.rule_bindings,
        request.endpoint_interfaces,
        request.scope_bindings,
        graph.subjects,
        contracts,
        graph,
    )
    return {
        "graph": graph,
        "contracts": contracts,
        "bindings": bindings,
        "interfaces": interfaces,
        "records": _seed_records(forward),
        "cacheBudget": OutputBudget(8 * 1024 * 1024),
    }


def replay_route(path, context, ledger, deadline, *, deadline_observation=None):
    witnesses = {ref: witness for ref, witness in path}
    records = context["records"]
    for witness_ref, witness in path:
        if witness_ref in records:
            continue
        record, error = _replay_witness(
            witness_ref, witness, witnesses, records, context, ledger, deadline,
            deadline_observation,
        )
        if error:
            return None, [error]
        records[witness_ref] = record
    return records.get(path[-1][0]) if path else None, []


def _replay_witness(witness_ref, witness, witnesses, records, context, ledger, deadline,
                    deadline_observation=None):
    if witness.get("sourceContractRef") is not None:
        return _source_record(witness, context)
    return _derived_record(witness_ref, witness, witnesses, records, context, ledger, deadline,
                           deadline_observation)


def _source_record(witness, context):
    source_ref = witness["sourceContractRef"]
    key = (source_ref.get("artifactRef"), source_ref.get("localId"))
    artifact = context["contracts"].get(key)
    interface = context["interfaces"].get(witness.get("interfaceId"))
    if artifact is None or interface is None or interface.get("contractRef") != source_ref:
        return None, {"code": "replay-source-binding-unresolved"}
    return artifact["payload"]["record"], None


def _derived_record(witness_ref, witness, witnesses, records, context, ledger, deadline,
                    deadline_observation=None):
    parent_refs = witness.get("parentWitnessRefs", [])
    prepared, error = _replay_application(witness, parent_refs, records, context)
    if error:
        return None, error
    step_ref, step, binding = prepared
    if not _reserve_record(parent_refs, records, context):
        return None, {
            "code": "replay-output-budget-exhausted",
            "stepRef": step_ref,
            "witnessRef": witness_ref,
        }
    if not _reserve(ledger, 1, deadline, step_ref, deadline_observation):
        return None, {
            "code": "replay-work-budget-exhausted",
            "stepRef": step_ref,
            "witnessRef": witness_ref,
        }
    combo = _replay_combo(parent_refs, witnesses, records)
    residuals = []
    output = _transfer(step, binding, combo, context["interfaces"], context["graph"], residuals)
    if output is None:
        return None, residuals[0] if residuals else {
            "code": "replay-transfer-unresolved",
            "stepRef": step_ref,
        }
    return output, None


def _replay_application(witness, parent_refs, records, context):
    if any(parent not in records for parent in parent_refs):
        return None, {"code": "replay-parent-witness-unavailable"}
    step_ref = witness.get("stepRef")
    if step_ref is None:
        return None, {"code": "replay-witness-kind-unavailable"}
    key = _refkey(step_ref)
    binding = context["bindings"].get(key)
    step = next((row for row in context["graph"].steps if _key(row["stepRef"]) == key), None)
    if binding is None or step is None:
        return None, {"code": "replay-rule-binding-unavailable", "stepRef": step_ref}
    return (step_ref, step, binding), None


def _replay_combo(parent_refs, witnesses, records):
    return tuple(
        {
            "contractRecord": records[parent],
            "routeWitnessRef": parent,
            "routeWitness": witnesses[parent],
        }
        for parent in parent_refs
    )


def _reserve(ledger, combinations, deadline, step_ref, observation=None):
    from datetime import UTC, datetime

    if observation is not None and observation.expired():
        return False
    if observation is None and deadline is not None and datetime.now(UTC) >= deadline:
        return False
    units = max(1, combinations)
    if ledger["stepsRemaining"] < 1 or units > ledger["combinationsRemaining"]:
        return False
    if units > ledger["maxCombinationsPerStep"]:
        return False
    ledger["stepsRemaining"] -= 1
    ledger["combinationsRemaining"] -= units
    ledger["plannerSteps"] += 1
    ledger["plannerCombinations"] += units
    ledger["totalSteps"] += 1
    ledger["totalCombinations"] += units
    ledger["plannerStepRefs"].append(step_ref)
    return True


def _seed_records(forward):
    return {
        ref: row["contractRecord"]
        for frontier in forward.get("frontiers", [])
        for row in frontier["contracts"]
        for ref in row.get("routeWitnessRefs", [])
    }


def _reserve_record(parent_refs, records, context):
    # A transfer record is at most the combined input feature material plus
    # its bounded changed interface identifiers. Prepay retained output and
    # validation's temporary copy before invoking the transfer.
    material = [records[parent] for parent in parent_refs]
    return context["cacheBudget"].reserve(material, copies=2, overhead=8192)
