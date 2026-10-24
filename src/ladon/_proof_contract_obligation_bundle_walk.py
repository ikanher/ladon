"""Build route-local demand graphs while processing backward queue edges."""

from ladon._contract_propagation_budget import fingerprint

from ._proof_contract_obligation_bundle import (
    add_alternative,
    add_demand,
    add_incoming,
    demand_id,
    finish_bundle,
    new_bundle,
)


def backward_bundle(path, desired, step_by_key, bindings, interfaces, choices, ledger,
                    deadline, bounds, output_budget, route_id, request_digest,
                    deadline_observation, backward_unit):
    witnesses = {ref: witness for ref, witness in path}
    bundle = new_bundle(route_id, request_digest)
    index = {}
    queue = [(path[-1][0], desired, None)] if path else []
    admitted = set()
    interface_by_id = {row["interfaceId"]: row for row in interfaces}
    root = add_demand(bundle, index, route_id, path[-1][0], desired, witnesses[path[-1][0]]) if path else None
    if root is not None:
        bundle["rootDemandId"] = root["demandId"]
        if not output_budget.reserve(root, overhead=8):
            root["status"] = "partial"
            pending = [{"demandId": root["demandId"], "reason": "output-size-cap"}]
            return [], [], pending, finish_bundle(bundle, pending, [])
    requirements, residuals, pending = [], [], []
    while queue:
        stopped = _process_queue_item(
            queue.pop(0), queue, witnesses, step_by_key, bindings, interfaces, choices, ledger,
            deadline, bounds, output_budget, route_id, bundle, index, admitted,
            interface_by_id, requirements, residuals, pending, deadline_observation,
            backward_unit,
        )
        if stopped:
            break
    return requirements, residuals, pending, finish_bundle(bundle, pending, residuals)


def _process_queue_item(item, queue, witnesses, step_by_key, bindings, interfaces, choices, ledger,
                        deadline, bounds, budget, route_id, bundle, index, admitted,
                        interface_by_id, requirements, residuals, pending, observer,
                        backward_unit):
    witness_ref, output, incoming = item
    demand = add_demand(bundle, index, route_id, witness_ref, output, witnesses[witness_ref])
    if incoming is not None and not add_incoming(demand, *incoming, budget):
        return _stop_demand(demand, "output-size-cap", pending)
    key = (witness_ref, fingerprint(output))
    if key in admitted:
        return False
    admitted.add(key)
    found, errors, reason = backward_unit(
        witness_ref, output, witnesses, step_by_key, bindings, interfaces, choices,
        interface_by_id, bounds, ledger, deadline, budget,
        deadline_observation=observer,
    )
    if reason:
        _stop_demand(demand, reason["reason"], pending)
        _queue_pending(queue, witnesses, route_id, bundle, index, pending,
                       reason["reason"])
        return True
    rows, stopped = found
    requirements.extend(rows)
    residuals.extend(errors)
    _set_demand_status(demand, rows, errors, witnesses[witness_ref])
    if rows:
        branch_stopped = _append_branches(
            demand, rows, witnesses[witness_ref], witnesses, route_id, bundle,
            index, budget, queue, pending,
        )
    else:
        branch_stopped = False
    branch_pending = _backward_budget_pending(errors, witnesses[witness_ref], witness_ref)
    if branch_pending or stopped or branch_stopped:
        reason = branch_pending["reason"] if branch_pending else "output-size-cap"
        _stop_demand(demand, reason, pending)
        _queue_pending(queue, witnesses, route_id, bundle, index, pending, reason)
        return True
    return False


def _append_branches(demand, rows, witness, witnesses, route_id, bundle, index, budget, queue,
                     pending):
    groups = _groups(rows)
    occurrences = witness.get("premiseOccurrences", [])
    for (branch_ref, branch_index), branch_rows in groups:
        edges = _branch_edges(
            demand, branch_ref, branch_rows, occurrences, witnesses, route_id, bundle,
            index, budget, queue, pending,
        )
        expected = list(range(len(occurrences)))
        if not add_alternative(demand, branch_ref, branch_index, edges, budget,
                               expected_ordinals=expected):
            _stop_demand(demand, "output-size-cap", pending)
            return True
        if len(edges) != len(expected):
            _stop_demand(demand, "incomplete-premise-occurrences", pending)
            return True
    return False


def _branch_edges(parent, branch_ref, rows, occurrences, witnesses, route_id, bundle, index,
                  budget, queue, pending):
    edges = []
    for row in sorted(rows, key=lambda item: item["premiseOrdinal"]):
        ordinal = row["premiseOrdinal"]
        if ordinal >= len(occurrences):
            raise ValueError("generated premise ordinal is outside its original application")
        child_ref = occurrences[ordinal].get("parentWitnessRef")
        if child_ref not in witnesses:
            pending.append({"demandId": parent["demandId"], "branchRef": branch_ref,
                            "premiseOrdinal": ordinal, "reason": "missing-child-witness"})
            continue
        _, edge = _child_edge(parent, branch_ref, row, child_ref, witnesses, route_id,
                              bundle, index, budget, queue, pending)
        if edge is not None:
            edges.append(edge)
    return edges


def _child_edge(parent, branch_ref, row, child_ref, witnesses, route_id, bundle, index,
                budget, queue, pending):
    output = row["contractRecord"]
    identity = demand_id(route_id, child_ref, output)
    fresh = identity not in index
    child = add_demand(bundle, index, route_id, child_ref, output, witnesses[child_ref])
    if fresh and not budget.reserve(child, overhead=8):
        _stop_demand(child, "output-size-cap", pending)
        return child, None
    ordinal = row["premiseOrdinal"]
    if not add_incoming(child, parent["demandId"], branch_ref, ordinal, budget):
        _stop_demand(child, "output-size-cap", pending)
        return child, None
    edge = {"premiseOrdinal": ordinal, "contractRecord": output,
            "childDemandId": child["demandId"],
            **{key: row[key] for key in ("interfaceId", "statementRef", "forwardContractRef")
               if key in row}}
    queue.append((child_ref, output, None))
    return child, edge


def _stop_demand(demand, reason, pending):
    demand["status"] = "partial"
    pending.append({"demandId": demand["demandId"], "reason": reason})
    return True


def _groups(rows):
    groups = {}
    for row in rows:
        groups.setdefault((row["branchRef"], row["branchIndex"]), []).append(row)
    return groups.items()


def _queue_pending(queue, witnesses, route_id, bundle, index, pending, reason):
    while queue:
        witness_ref, output, _ = queue.pop(0)
        demand = add_demand(bundle, index, route_id, witness_ref, output, witnesses[witness_ref])
        _stop_demand(demand, reason, pending)


def _set_demand_status(demand, rows, errors, witness):
    if "stepRef" not in witness:
        demand["status"] = "requires-source-check"
    elif not rows:
        demand["status"] = "unsupported" if errors else "generated"
    else:
        demand["status"] = "generated"


def _backward_budget_pending(errors, witness, witness_ref):
    if not any(row.get("code") == "backward-budget-exhausted" for row in errors):
        return None
    return {"stepRef": witness.get("stepRef"), "branchRef": witness_ref,
            "reason": "backward-branch-budget"}
