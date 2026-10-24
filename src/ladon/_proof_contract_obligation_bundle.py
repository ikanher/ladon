"""Bounded identifiers and records for planner-v2 route demand graphs."""

from ladon._contract_propagation_budget import fingerprint


def demand_id(route_id, witness_ref, output):
    return "sha256:" + fingerprint([route_id, witness_ref, output]).hex()


def new_bundle(route_id, request_digest):
    return {
        "schema": "ladon-route-obligation-bundle-v1",
        "routeId": route_id,
        "requestDigest": request_digest,
        "rootDemandId": None,
        "demands": [],
        "residuals": [],
        "pending": [],
        "status": "generated",
        "checkerAuthority": "none",
        "wholeMethodAuthority": "none",
    }


def add_demand(bundle, index, route_id, witness_ref, output, witness):
    identity = demand_id(route_id, witness_ref, output)
    row = index.get(identity)
    if row is None:
        source = witness.get("sourceContractRef") is not None or "stepRef" not in witness
        row = {
            "demandId": identity,
            "witnessRef": witness_ref,
            "outputContractDigest": "sha256:" + fingerprint(output).hex(),
            "status": "requires-source-check" if source else "pending",
            "alternatives": [],
            "incomingOccurrences": [],
        }
        index[identity] = row
        bundle["demands"].append(row)
    return row


def add_incoming(child, parent_id, branch_ref, ordinal, budget):
    occurrence = {
        "parentDemandId": parent_id,
        "branchRef": branch_ref,
        "premiseOrdinal": ordinal,
    }
    if not budget.reserve(occurrence, overhead=8):
        return False
    child["incomingOccurrences"].append(occurrence)
    return True


def add_alternative(parent, branch_ref, branch_index, requirements, budget,
                    *, expected_ordinals=None):
    present = {row["premiseOrdinal"] for row in requirements}
    expected = sorted(present) if expected_ordinals is None else list(expected_ordinals)
    missing = [ordinal for ordinal in expected if ordinal not in present]
    alternative = {
        "branchRef": branch_ref,
        "branchIndex": branch_index,
        "requirements": requirements,
        "status": "partial" if missing else "generated",
        "expectedPremiseOrdinals": expected,
        "pendingPremiseOrdinals": missing,
    }
    if not budget.reserve(alternative, overhead=8):
        return False
    parent["alternatives"].append(alternative)
    return True


def finish_bundle(bundle, pending, residuals):
    bundle["pending"] = list(pending)
    bundle["residuals"] = list(residuals)
    if pending or any(row["status"] == "partial" for row in bundle["demands"]):
        bundle["status"] = "partial"
    elif not bundle["demands"] or all(
        row["status"] == "unsupported" for row in bundle["demands"]
    ):
        bundle["status"] = "unsupported"
    return bundle
