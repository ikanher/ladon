"""Native comparison producers with explicitly conditional profile authority."""

from ladon.proof_contract_rules import PROFILE_DIGEST
from ladon.proofir_v3 import make_envelope, validate_envelope


def comparison_artifact(left, right, *, analysis_id):
    from ladon.proof_contracts import compare_contracts

    inputs = [validate_envelope(v).to_dict() for v in (left, right)]
    if any(v["artifactKind"] != "proofir.contract" for v in inputs):
        raise ValueError("comparison requires native contracts")
    if inputs[0]["environmentRef"] != inputs[1]["environmentRef"]:
        raise ValueError("comparison cannot cross environments without a checked bridge")
    refs = [{"artifactRef": v["artifactId"], "kind": "contract",
             "localId": v["payload"]["contractId"]} for v in inputs]
    payload = {
        "analysisId": analysis_id, "profileDigest": PROFILE_DIGEST, "stage": "comparison",
        "contractRefs": refs,
        "result": compare_contracts(inputs[0]["payload"]["record"],
                                    inputs[1]["payload"]["record"]),
        "checkRunRefs": [], "residuals": [],
    }
    return make_envelope(
        artifact_kind="proofir.contract-analysis",
        producer={"name": "ladon-contract-comparison", "version": "1"},
        environment_ref=inputs[0]["environmentRef"],
        subject_refs=[{"kind": "contract-analysis", "localId": analysis_id}],
        coverage={"status": "complete", "observed": 1}, payload=payload,
        limitations=[{"id": "conditional-contract-profile", "message":
                      "Structural comparison assumes the declared profile; no source fidelity, "
                      "exact application acceptance or mathematical falsity is established."},
                     {"id": "source-contract-binding-unchecked", "message":
                      "A shared abstract endpoint does not establish faithful interpretation "
                      "or implication between the original source propositions."}],
    ).to_dict()


def propagation_artifact(
    graph, contracts, *, analysis_id, goal_ref, rule_bindings,
    endpoint_interfaces, scope_bindings=(), bounds=None,
):
    """Bind a conditional propagation result to its exact native graph inputs."""
    from ladon.proof_contract_propagation import propagate_contracts

    inputs = _prepare_propagation_inputs(
        graph, contracts, analysis_id, goal_ref, rule_bindings,
        endpoint_interfaces, scope_bindings, bounds,
    )
    result = propagate_contracts(
        inputs["derivation"], inputs["contracts"], goal_ref=goal_ref,
        rule_bindings=inputs["rules"], endpoint_interfaces=inputs["interfaces"],
        scope_bindings=inputs["scopes"], bounds=bounds,
    )
    return _make_propagation_envelope(analysis_id, goal_ref, inputs, result, bounds)


def _prepare_propagation_inputs(
    graph, contracts, analysis_id, goal_ref, rule_bindings,
    endpoint_interfaces, scope_bindings, bounds,
):
    from ladon._contract_propagation_input_budget import input_bytes_exceeded
    from ladon._contract_propagation_inputs import preflight_size, read_bounds, read_contracts
    from ladon._contract_propagation_validation import _validate_inputs
    from ladon._proofir_derivation_core import _Graph
    from ladon.proof_contract_propagation import _goal_shape

    _goal_shape(goal_ref)
    raw_inputs = [graph, contracts, analysis_id, goal_ref, rule_bindings,
                  endpoint_interfaces, scope_bindings, bounds]
    if input_bytes_exceeded(raw_inputs) is not None:
        raise ValueError("aggregate propagation input exceeds the fixed 8 MiB limit")
    read_bounds(bounds)
    preflight_size(graph, contracts, rule_bindings, endpoint_interfaces, scope_bindings)
    derivation = validate_envelope(graph).to_dict()
    checked_contracts = [validate_envelope(row).to_dict() for row in contracts]
    if derivation["artifactKind"] != "proofir.derivation":
        raise ValueError("propagation requires one native derivation")
    if any(row["artifactKind"] != "proofir.contract" for row in checked_contracts):
        raise ValueError("propagation inputs must be native contracts")
    if any(row["environmentRef"] != derivation["environmentRef"] for row in checked_contracts):
        raise ValueError("propagation cannot cross environments without a checked bridge")
    native_graph = _Graph.build(derivation)
    _goal, error = native_graph.local_ref(goal_ref, "/goalRef")
    if error:
        raise ValueError(error["message"])
    contract_index = read_contracts(checked_contracts, derivation["environmentRef"])
    rules = list(rule_bindings)
    interfaces = list(endpoint_interfaces)
    scopes = list(scope_bindings)
    _validate_inputs(
        rules, interfaces, scopes, native_graph.subjects, contract_index, native_graph
    )
    return {
        "derivation": derivation,
        "contracts": checked_contracts,
        "rules": rules,
        "interfaces": interfaces,
        "scopes": scopes,
    }


def _make_propagation_envelope(analysis_id, goal_ref, inputs, result, bounds):
    derivation = inputs["derivation"]
    checked_contracts = inputs["contracts"]
    request = {
        "goalRef": goal_ref,
        "ruleBindings": inputs["rules"],
        "endpointInterfaces": inputs["interfaces"],
        "scopeBindings": inputs["scopes"],
        "bounds": bounds,
    }
    contract_refs = [
        {"artifactRef": row["artifactId"], "kind": "contract", "localId": row["payload"]["contractId"]}
        for row in checked_contracts
    ]
    payload = {
        "analysisId": analysis_id,
        "profileDigest": PROFILE_DIGEST,
        "stage": "propagation",
        "derivationGoalRef": {"artifactRef": derivation["artifactId"], **goal_ref},
        "contractRefs": contract_refs,
        "request": request,
        "result": result,
        "checkRunRefs": [],
        "residuals": [],
    }
    coverage_status = "complete" if result["complete"] else "partial"
    return make_envelope(
        artifact_kind="proofir.contract-analysis",
        producer={"name": "ladon-contract-propagation", "version": "1"},
        environment_ref=derivation["environmentRef"],
        subject_refs=[{"kind": "contract-analysis", "localId": analysis_id}],
        coverage={"status": coverage_status, "observed": 1},
        payload=payload,
        limitations=[
            {"id": "conditional-contract-profile", "message": "Propagation is a bounded profile summary."},
            {"id": "source-contract-binding-unchecked", "message": "Source fidelity and mathematical implication are not established."},
            {"id": "deadline-observation-unverified", "message": "Recorded deadline decisions support deterministic replay only; wall-clock time is not authenticated."},
        ],
    ).to_dict()


def source_contract_artifact(record, *, contract_id, environment_ref, source_map_refs,
                             mode="authored", residuals=()):
    """Attach a summary to source maps without asserting source fidelity."""
    from ladon.proof_contracts import validate_contract

    checked = validate_contract(record)
    statement = {"kind": "statement", "localId": "statement:" + contract_id}
    assumptions = [{"kind": "statement", "localId": r["predicateId"]}
                   for r in checked["assumptions"]]
    conclusion = {"kind": "statement", "localId": checked["conclusionId"]}
    own = [{"kind": "contract", "localId": contract_id}, statement, conclusion, *assumptions]
    subjects = {(r["kind"], r["localId"]): r for r in own}
    payload = {
        "contractId": contract_id, "profileDigest": PROFILE_DIGEST, "record": checked,
        "statementRef": statement, "assumptionRefs": assumptions, "conclusionRef": conclusion,
        "sourceMapRefs": list(source_map_refs), "checkRunRefs": [],
        "provenance": {"mode": mode, "fidelity": "attributed-unreviewed",
                       "completeness": "partial" if residuals else "complete",
                       "checkerAuthority": "none", "mathematicalFalsity": "not-established"},
        "residuals": list(residuals),
    }
    return make_envelope(
        artifact_kind="proofir.contract",
        producer={"name": "ladon-contract-source", "version": "1"},
        environment_ref=environment_ref, subject_refs=[subjects[k] for k in sorted(subjects)],
        coverage={"status": "complete", "observed": len(subjects)}, payload=payload,
        limitations=[{"id": "source-contract-binding-unchecked", "message":
                      "Source-bound contract features remain an attributed interpretation."}],
    ).to_dict()
