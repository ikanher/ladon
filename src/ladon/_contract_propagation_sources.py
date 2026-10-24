"""Source contract bindings and immutable shared witness construction."""

from ladon._contract_propagation_common import _canonical, _external
from ladon._contract_propagation_transfer import _input_interface_matches, _route_evidence
from ladon._proofir_derivation_core import _ref


def _scope_matches(scope, record, interface):
    if interface is None or not _input_interface_matches(interface, record):
        return False
    objects = scope["objectMap"]
    if objects != [
        {"fromObjectId": record["context"]["objectId"], "toObjectId": interface["objectId"]}
    ]:
        return False
    binders = {row["fromBinderId"]: row["toBinderId"] for row in scope["binderMap"]}
    return binders == {row["binderId"]: row["binderId"] for row in record["telescope"]}


def source_rows(state, statement):
    output = []
    for scope in sorted(state.scopes.get(statement, []), key=_canonical):
        if state.stop("deadline", statement, reached=state.expired()):
            break
        if state.witness_budget_exhausted(statement):
            break
        ext = scope["contractRef"]
        artifact = state.contracts[(ext["artifactRef"], ext["localId"])]
        record = artifact["payload"]["record"]
        if not state.budget.admits(record):
            break
        interface = state.source_interfaces.get((ext["artifactRef"], ext["localId"]))
        if not _scope_matches(scope, record, interface):
            state.residuals.append(
                {"code": "unsupported-source-scope-transport", "statementRef": _ref(statement)}
            )
            continue
        witness = {
            "sourceContractRef": _external(artifact),
            "sourceStatementRef": _ref(statement),
            "interfaceId": interface["interfaceId"],
            "localContextRef": scope["localContextRef"],
            "objectMap": scope["objectMap"],
            "binderMap": scope["binderMap"],
            "substitutionRefs": scope["substitutionRefs"],
            "evidenceRefs": scope["evidenceRefs"],
            "premiseOccurrences": [],
            "parentWitnessRefs": [],
        }
        row = state.route_row(record, witness)
        if row is None:
            break
        output.append(row)
    return output


def application_witness(step, binding, combo, interfaces):
    occurrences = []
    for ordinal, premise in enumerate(step["premiseRefs"]):
        item = combo[ordinal]
        contract = item["routeWitness"].get("sourceContractRef")
        if contract is None:
            contract = {"kind": "contract-route", "localId": item["routeWitnessRef"]}
        occurrences.append(
            {
                "ordinal": ordinal,
                "statementRef": premise,
                "contractRef": contract,
                "parentWitnessRef": item["routeWitnessRef"],
            }
        )
    return {
        "stepRef": step["stepRef"],
        "ruleRef": step["ruleRef"],
        "localContextRef": step["localContextRef"],
        "substitutionRefs": [row["termRef"] for row in step["substitutions"]],
        "interfaceId": binding["outputInterfaceId"],
        "premiseOccurrences": occurrences,
        "parentWitnessRefs": [item["routeWitnessRef"] for item in combo],
        "evidenceRefs": _route_evidence(binding, combo, interfaces),
    }
