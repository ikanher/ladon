"""Closed native mathematical-contract payloads; no checker authority is inferred."""

from ladon.proof_contract_rules import PROFILE_DIGEST
from ladon.proofir_v3 import _require_ref


def closed(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{label} requires exactly {sorted(keys)}")


def identifier(value, label):
    if not isinstance(value, str) or not value or len(value.encode()) > 512:
        raise ValueError(f"invalid bounded {label}")


def rows(value, label, *, minimum=0):
    if not isinstance(value, list) or not minimum <= len(value) <= 4096:
        raise ValueError(f"invalid bounded {label} collection")


def residuals(value):
    rows(value, "residuals")
    for row in value:
        closed(row, {"code", "message", "feature"}, "residual")
        for key, text in row.items():
            identifier(text, key)


def provenance(value, record, remaining):
    closed(value, {"mode", "fidelity", "completeness", "checkerAuthority",
                   "mathematicalFalsity"}, "provenance")
    if value["mode"] not in {"authored", "extracted", "derived"}:
        raise ValueError("unsupported contract provenance mode")
    if (value["fidelity"] != "attributed-unreviewed"
            or value["checkerAuthority"] != "none"
            or value["mathematicalFalsity"] != "not-established"):
        raise ValueError("contract provenance cannot promote semantic authority")
    if value["completeness"] not in {"complete", "partial"}:
        raise ValueError("invalid contract completeness")
    features = record["features"]
    states = [features["regularity"]["state"], features["constantDependencies"]["state"]]
    states.extend(row["state"] for row in features["witnessDependencies"])
    if value["completeness"] == "complete" and (remaining or set(states) != {"known"}):
        raise ValueError("incomplete contract features require partial coverage")


def _refs(p, field, kind, value, subjects, env, *, minimum=0):
    rows(p[field], field, minimum=minimum)
    for index, ref in enumerate(p[field]):
        if not isinstance(ref, dict) or ref.get("kind") != kind:
            raise ValueError(f"{field} requires {kind} references")
        _require_ref(ref, f"/payload/{field}/{index}", subjects, env, value, kind)


def validate_contract_payload(p, value, subjects, env):
    from ladon.proof_contracts import validate_contract

    closed(p, {"contractId", "profileDigest", "record", "statementRef", "assumptionRefs",
               "conclusionRef", "sourceMapRefs", "checkRunRefs", "provenance", "residuals"},
           "contract payload")
    identifier(p["contractId"], "contract ID")
    if ("contract", p["contractId"]) not in subjects:
        raise ValueError("contract must own its exact typed subject")
    if p["profileDigest"] != PROFILE_DIGEST:
        raise ValueError("contract profile digest mismatch")
    record = validate_contract(p["record"])
    for field in ("statementRef", "conclusionRef"):
        if not isinstance(p[field], dict) or p[field].get("kind") != "statement":
            raise ValueError(f"{field} requires a statement reference")
        _require_ref(p[field], f"/payload/{field}", subjects, env, value, "statement")
    if p["conclusionRef"]["localId"] != record["conclusionId"]:
        raise ValueError("contract conclusion reference differs from record")
    _refs(p, "assumptionRefs", "statement", value, subjects, env)
    if [r["localId"] for r in p["assumptionRefs"]] != [
            r["predicateId"] for r in record["assumptions"]]:
        raise ValueError("contract assumption references differ from record")
    _refs(p, "sourceMapRefs", "source-map", value, subjects, env, minimum=1)
    _refs(p, "checkRunRefs", "check-run", value, subjects, env)
    residuals(p["residuals"])
    provenance(p["provenance"], record, p["residuals"])


def validate_analysis_payload(p, value, subjects, env):
    from ladon._proof_contract_payload_analysis import validate_analysis_payload as validate

    return validate(p, value, subjects, env)


def _validate_comparison_payload(p, value, subjects, env):
    closed(p, {"analysisId", "profileDigest", "stage", "contractRefs", "result",
               "checkRunRefs", "residuals"}, "analysis payload")
    identifier(p["analysisId"], "analysis ID")
    if "source-contract-binding-unchecked" not in {r["id"] for r in value["limitations"]}:
        raise ValueError("comparison requires the source-contract-binding-unchecked limitation")
    if ("contract-analysis", p["analysisId"]) not in subjects:
        raise ValueError("analysis must own its exact typed subject")
    if p["profileDigest"] != PROFILE_DIGEST or p["stage"] != "comparison":
        raise ValueError("unsupported contract analysis profile or stage")
    _refs(p, "contractRefs", "contract", value, subjects, env, minimum=2)
    if len(p["contractRefs"]) != 2 or any("artifactRef" not in r for r in p["contractRefs"]):
        raise ValueError("comparison requires two external contract references")
    _comparison_result(p["result"])
    _refs(p, "checkRunRefs", "check-run", value, subjects, env)
    residuals(p["residuals"])


def _validate_propagation_payload(p, value, subjects, env):
    closed(p, {"analysisId", "profileDigest", "stage", "derivationGoalRef", "contractRefs",
               "request", "result", "checkRunRefs", "residuals"}, "propagation payload")
    identifier(p["analysisId"], "analysis ID")
    if ("contract-analysis", p["analysisId"]) not in subjects:
        raise ValueError("analysis must own its exact typed subject")
    if p["profileDigest"] != PROFILE_DIGEST:
        raise ValueError("propagation profile digest mismatch")
    _require_ref(p["derivationGoalRef"], "/payload/derivationGoalRef", subjects, env, value, "statement")
    _refs(p, "contractRefs", "contract", value, subjects, env)
    _validate_propagation_request(p["request"])
    result = p["result"]
    if not isinstance(result, dict):
        raise TypeError("propagation result must be an object")
    _validate_propagation_result(result, p["request"])
    expected_status = "complete" if result["complete"] else "partial"
    if value["coverage"]["status"] != expected_status:
        raise ValueError("propagation envelope coverage differs from its result")
    _refs(p, "checkRunRefs", "check-run", value, subjects, env)
    residuals(p["residuals"])
    if "source-contract-binding-unchecked" not in {row["id"] for row in value["limitations"]}:
        raise ValueError("propagation requires the source-contract-binding-unchecked limitation")
    if "deadline-observation-unverified" not in {row["id"] for row in value["limitations"]}:
        raise ValueError("propagation requires the deadline-observation-unverified limitation")


def _validate_propagation_request(request):
    closed(request, {"goalRef", "ruleBindings", "endpointInterfaces", "scopeBindings", "bounds"},
           "propagation request")
    _require_local_statement_ref(request["goalRef"], "propagation goal")
    for key in ("ruleBindings", "endpointInterfaces", "scopeBindings"):
        rows(request[key], key)
    if request["bounds"] is not None and not isinstance(request["bounds"], dict):
        raise ValueError("propagation bounds must be an object or null")


def _require_local_statement_ref(ref, label):
    if not isinstance(ref, dict) or set(ref) != {"kind", "localId"}:
        raise ValueError(f"{label} must be an exact local reference")
    if ref["kind"] != "statement":
        raise ValueError(f"{label} must name a statement")
    identifier(ref["localId"], label)


def _validate_deadline_observation(result):
    if "deadlineObservation" not in result:
        raise ValueError("propagation result is missing its deadline observation")
    from ladon._contract_propagation_deadline import validate_deadline_trace

    validate_deadline_trace(result["deadlineObservation"])


def _validate_propagation_result(result, request):
    _validate_result_shape(result)
    _validate_result_identity(result, request)
    _validate_result_status(result)
    _validate_result_content(result)


def _validate_result_shape(result):
    common = {
        "analysisId", "schema", "status", "complete", "goalRef", "frontiers",
        "prunings", "residuals", "coverage", "witnesses", "profileDigest",
        "authority", "mathematicalFalsity", "limitations", "deadlineObservation",
    }
    if set(result) == common | {"analysisInputs"}:
        _validate_complete_result_shape(result)
    elif set(result) == common | {"analysisInputDigest"}:
        identifier(result["analysisInputDigest"], "analysis input digest")
    else:
        raise ValueError("propagation result has unexpected or missing fields")


def _validate_result_identity(result, request):
    identifier(result["analysisId"], "propagation result ID")
    if result["schema"] != "ladon-contract-propagation-v1":
        raise ValueError("propagation result schema mismatch")
    if result["profileDigest"] != PROFILE_DIGEST or result["authority"] != "conditional-profile":
        raise ValueError("propagation result profile or authority mismatch")
    if result["mathematicalFalsity"] != "not-established":
        raise ValueError("propagation cannot claim mathematical falsity")
    if "source-contract-binding-unchecked" not in result["limitations"]:
        raise ValueError("propagation result is missing its source-fidelity limitation")
    _require_local_statement_ref(result["goalRef"], "propagation result goal")
    if result["goalRef"] != request["goalRef"]:
        raise ValueError("propagation result goal differs from its request")


def _validate_result_status(result):
    if type(result["complete"]) is not bool:
        raise ValueError("propagation result completeness must be Boolean")
    if result["complete"] and result["status"] != "complete":
        raise ValueError("propagation result status differs from completeness")
    if not result["complete"] and result["status"] not in {"partial", "unsupported-cycle"}:
        raise ValueError("propagation result status is invalid")


def _validate_result_content(result):
    for field in ("frontiers", "prunings", "residuals", "witnesses", "limitations"):
        rows(result[field], f"result.{field}")
    _validate_result_coverage(result["coverage"])
    _validate_deadline_observation(result)

def _validate_complete_result_shape(result):
    if not isinstance(result["analysisInputs"], dict):
        raise TypeError("propagation analysisInputs must be an object")


def _validate_result_coverage(coverage):
    closed(coverage, {"counts", "pending"}, "propagation result coverage")
    closed(coverage["counts"], {"steps", "combinations", "references"}, "propagation counts")
    for value in coverage["counts"].values():
        if type(value) is not int or value < 0:
            raise ValueError("propagation coverage counts must be nonnegative integers")
    rows(coverage["pending"], "propagation pending")


def _comparison_result(result):
    closed(result, {"relation", "reasons", "authority", "mathematicalFalsity"},
           "comparison result")
    if result["relation"] not in {
            "dominates", "dominated", "equivalent", "incomparable", "unknown"}:
        raise ValueError("invalid comparison relation")
    rows(result["reasons"], "comparison reasons")
    for reason in result["reasons"]:
        identifier(reason, "comparison reason")
    if (result["authority"] != "profile-structural"
            or result["mathematicalFalsity"] != "not-established"):
        raise ValueError("comparison cannot promote authority")


def validate_analysis_inputs(artifact, artifacts):
    """Recompute the summary from exact batch-owned inputs, never from labels."""
    if artifact["artifactKind"] != "proofir.contract-analysis":
        return
    return _recompute_analysis_stage(artifacts, artifact["payload"])


def _recompute_analysis_stage(artifacts, payload):
    from ladon._proof_contract_payload_analysis import _recompute_analysis_stage

    return _recompute_analysis_stage(artifacts, payload)


def _recompute_contract_comparison(artifacts, payload):
    from ladon.proof_contracts import compare_contracts

    inputs = [artifacts[r["artifactRef"]] for r in payload["contractRefs"]]
    for ref, source in zip(payload["contractRefs"], inputs, strict=True):
        if (source["artifactKind"] != "proofir.contract"
                or source["payload"]["contractId"] != ref["localId"]):
            raise ValueError("comparison input must be the exact contract owner")
    expected = compare_contracts(inputs[0]["payload"]["record"], inputs[1]["payload"]["record"])
    if payload["result"] != expected:
        raise ValueError("comparison result differs from exact input recomputation")


def _recompute_propagation(artifacts, payload):
    graph_ref = payload["derivationGoalRef"]
    graph = artifacts[graph_ref["artifactRef"]]
    if graph["artifactKind"] != "proofir.derivation":
        raise ValueError("propagation graph owner must be a derivation")
    graph_subjects = {(row["kind"], row["localId"]) for row in graph["subjectRefs"]}
    if (graph_ref["kind"], graph_ref["localId"]) not in graph_subjects:
        raise ValueError("propagation goal must be owned by the exact derivation")
    contracts = [artifacts[row["artifactRef"]] for row in payload["contractRefs"]]
    _validate_contract_owners(payload["contractRefs"], contracts)
    request = payload["request"]
    if request["goalRef"] != {key: graph_ref[key] for key in ("kind", "localId")}:
        raise ValueError("request goal differs from its exact derivation owner")
    _prevalidate_native_request(graph, contracts, request)
    result = payload["result"]
    expected = _propagate_from_request(graph, contracts, request, result["deadlineObservation"])
    if result != expected:
        raise ValueError("propagation result differs from exact input replay")


def _prevalidate_native_request(graph, contracts, request):
    from ladon._contract_propagation_input_budget import input_bytes_exceeded
    from ladon._contract_propagation_inputs import preflight_size, read_bounds, read_contracts
    from ladon._contract_propagation_validation import _validate_inputs
    from ladon._proofir_derivation_core import _Graph
    from ladon.proof_contract_propagation import _goal_shape

    if input_bytes_exceeded([graph, contracts, request]) is not None:
        raise ValueError("aggregate propagation input exceeds the fixed 8 MiB limit")
    _goal_shape(request["goalRef"])
    read_bounds(request["bounds"])
    preflight_size(
        graph, contracts, request["ruleBindings"], request["endpointInterfaces"],
        request["scopeBindings"],
    )
    checked_graph = _Graph.build(graph)
    _, error = checked_graph.local_ref(request["goalRef"], "/goalRef")
    if error:
        raise ValueError(error["message"])
    contract_index = read_contracts(contracts, graph["environmentRef"])
    _validate_inputs(
        request["ruleBindings"], request["endpointInterfaces"], request["scopeBindings"],
        checked_graph.subjects, contract_index, checked_graph,
    )


def _validate_contract_owners(references, contracts):
    for ref, source in zip(references, contracts, strict=True):
        if (source["artifactKind"] != "proofir.contract"
                or source["payload"]["contractId"] != ref["localId"]):
            raise ValueError("propagation input must be the exact contract owner")


def _propagate_from_request(graph, contracts, request, replay):
    from ladon.proof_contract_propagation import _propagate_contracts

    return _propagate_contracts(
        graph, contracts, goal_ref=request["goalRef"],
        rule_bindings=request["ruleBindings"],
        endpoint_interfaces=request["endpointInterfaces"],
        scope_bindings=request["scopeBindings"], bounds=request["bounds"],
        _deadline_replay=replay,
    )
