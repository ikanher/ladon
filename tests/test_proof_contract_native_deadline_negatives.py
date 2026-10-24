from copy import deepcopy

import pytest
from test_proof_contract_propagation_native import inputs

from ladon.proof_contract_artifacts import propagation_artifact
from ladon.proofir_v3 import make_envelope, validate_envelope_batch


def remade(original, payload):
    return make_envelope(
        artifact_kind=original["artifactKind"],
        producer=original["producer"],
        environment_ref=original["environmentRef"],
        subject_refs=original["subjectRefs"],
        coverage=original["coverage"],
        limitations=original["limitations"],
        payload=payload,
    ).to_dict()


def test_native_validation_rejects_extra_recorded_deadline_checks():
    graph, contracts, request = inputs()
    request["bounds"] = {"deadlineUtc": "2100-01-01T00:00:00Z"}
    result = propagation_artifact(graph, contracts, analysis_id="analysis:trace", **request)
    payload = deepcopy(result["payload"])
    payload["result"]["deadlineObservation"]["checks"] += 1
    altered = remade(result, payload)
    with pytest.raises(ValueError, match="deadline replay|result differs"):
        validate_envelope_batch([graph, *contracts, altered])


def test_native_validation_rejects_deadline_trace_without_first_exceeded_check():
    graph, contracts, request = inputs()
    request["bounds"] = {"deadlineUtc": "2000-01-01T00:00:00Z"}
    result = propagation_artifact(graph, contracts, analysis_id="analysis:expired", **request)
    assert result["payload"]["result"]["deadlineObservation"]["firstExceededCheck"] is not None
    payload = deepcopy(result["payload"])
    payload["result"]["deadlineObservation"]["firstExceededCheck"] = None
    altered = remade(result, payload)
    with pytest.raises(ValueError, match="deadline replay|result differs"):
        validate_envelope_batch([graph, *contracts, altered])


def test_artifact_constructor_rejects_mismatched_owned_goal():
    graph, contracts, request = inputs()
    request["goal_ref"] = {"kind": "statement", "localId": "statement:missing"}
    with pytest.raises(ValueError, match="query reference"):
        propagation_artifact(graph, contracts, analysis_id="analysis:bad-goal", **request)


def test_expired_deadline_does_not_skip_closed_wrapper_validation():
    graph, contracts, request = inputs()
    request["bounds"] = {"deadlineUtc": "2000-01-01T00:00:00Z"}
    request["scope_bindings"] = [{}]
    with pytest.raises(ValueError, match="scope_bindings.*exactly"):
        propagation_artifact(graph, contracts, analysis_id="analysis:bad-scope", **request)


def test_batch_replay_rejects_rehashed_expired_artifact_with_malformed_scope():
    graph, contracts, request = inputs()
    request["bounds"] = {"deadlineUtc": "2000-01-01T00:00:00Z"}
    result = propagation_artifact(graph, contracts, analysis_id="analysis:expired-good", **request)
    payload = deepcopy(result["payload"])
    payload["request"]["scopeBindings"] = [{}]
    altered = remade(result, payload)
    with pytest.raises(ValueError, match="scope_bindings.*exactly"):
        validate_envelope_batch([graph, *contracts, altered])


def test_native_factory_rejects_cross_environment_contract_owner():
    graph, contracts, request = inputs()
    source = contracts[0]
    foreign = make_envelope(
        artifact_kind=source["artifactKind"],
        producer=source["producer"],
        environment_ref="sha256:" + "1" * 64,
        subject_refs=source["subjectRefs"],
        coverage=source["coverage"],
        limitations=source["limitations"],
        payload=source["payload"],
    ).to_dict()
    with pytest.raises(ValueError, match="cannot cross environments"):
        propagation_artifact(graph, [foreign], analysis_id="analysis:foreign", **request)


def test_native_factory_stops_at_aggregate_input_byte_cap_before_validation():
    graph, contracts, request = inputs()
    request["scope_bindings"] = ["x" * (8 * 1024**2 + 1)]
    with pytest.raises(ValueError, match="fixed 8 MiB limit"):
        propagation_artifact(graph, contracts, analysis_id="analysis:oversized", **request)


def test_single_native_envelope_rejects_authority_promotion():
    graph, contracts, request = inputs()
    result = propagation_artifact(graph, contracts, analysis_id="analysis:authority", **request)
    payload = deepcopy(result["payload"])
    payload["result"]["authority"] = "formal"
    with pytest.raises(ValueError, match="profile or authority"):
        remade(result, payload)


def test_expired_artifact_preserves_the_exact_bounds_request():
    graph, contracts, request = inputs()
    request["bounds"] = {
        "deadlineUtc": "2000-01-01T00:00:00Z",
        "maxEvaluatedSteps": 32,
    }
    artifact = propagation_artifact(graph, contracts, analysis_id="analysis:bounds", **request)
    assert artifact["payload"]["request"]["bounds"] == request["bounds"]
    validate_envelope_batch([graph, *contracts, artifact])
