"""Native propagation binds exact graph inputs and replays recorded work."""

import sqlite3
from copy import deepcopy

import pytest
from support.proofir_v3_native import ref
from test_proof_contract_propagation import (
    _binding,
    _contract,
    _derivation,
    _interface,
    _scope,
    _step,
)

from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database
from ladon.proofir_v3 import make_envelope, validate_envelope_batch


def inputs():
    source = _contract("a")
    step = _step("one", ["statement:a"], "statement:goal")
    graph = _derivation([step])
    request = {"goal_ref": ref("statement", "statement:goal"),
               "rule_bindings": [_binding(step)],
               "endpoint_interfaces": [_interface("in", contract=source), _interface("out")],
               "scope_bindings": [_scope(source, statement="statement:a")]}
    return graph, [source], request


def artifact(graph, contracts, request):
    from ladon.proof_contract_artifacts import propagation_artifact

    return propagation_artifact(graph, contracts, analysis_id="analysis:propagate", **request)


def remade(original, payload):
    return make_envelope(
        artifact_kind=original["artifactKind"], producer=original["producer"],
        environment_ref=original["environmentRef"], subject_refs=original["subjectRefs"],
        coverage=original["coverage"], limitations=original["limitations"], payload=payload,
    ).to_dict()


def test_native_propagation_replays_exact_owned_graph_and_contracts():
    graph, contracts, request = inputs()
    result = artifact(graph, contracts, request)
    assert result["payload"]["stage"] == "propagation"
    assert result["payload"]["derivationGoalRef"] == {
        "artifactRef": graph["artifactId"], **request["goal_ref"],
    }
    assert result["payload"]["result"]["complete"] is True
    validate_envelope_batch([graph, *contracts, result])
    assert artifact(graph, contracts, request) == result


def test_native_propagation_rejects_rehashed_fabricated_frontier():
    graph, contracts, request = inputs()
    result = artifact(graph, contracts, request)
    payload = deepcopy(result["payload"])
    goal = next(row for row in payload["result"]["frontiers"]
                if row["statementRef"] == request["goal_ref"])
    goal["contracts"][0]["contractRecord"]["features"]["regularity"]["offset"] = 42
    altered = remade(result, payload)
    with pytest.raises(ValueError):
        validate_envelope_batch([graph, *contracts, altered])


def test_native_propagation_rejects_same_local_goal_under_different_owner():
    graph, contracts, request = inputs()
    result = artifact(graph, contracts, request)
    other_graph = deepcopy(graph)
    other_graph["producer"]["name"] += "-other"
    from ladon.proofir_v3 import detached_content_id

    other_graph["artifactId"] = detached_content_id(other_graph)
    with pytest.raises(ValueError):
        validate_envelope_batch([other_graph, *contracts, result])


def test_native_replay_uses_recorded_deadline_decisions_without_observing_current_clock(monkeypatch):
    graph, contracts, request = inputs()
    request["bounds"] = {"deadlineUtc": "2100-01-01T00:00:00Z"}
    result = artifact(graph, contracts, request)
    import ladon._contract_propagation_deadline as deadline

    def forbidden_clock():
        raise AssertionError("snapshot replay must not read the current wall clock")

    monkeypatch.setattr(deadline, "_utc_now", forbidden_clock)
    validate_envelope_batch([graph, *contracts, result])
    assert result["payload"]["result"]["deadlineObservation"]["firstExceededCheck"] is None


def test_native_projection_preserves_exact_derivation_goal_and_named_lookup_index():
    graph, contracts, request = inputs()
    result = artifact(graph, contracts, request)
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, [graph, *contracts, result])
    validate_v3_database(connection)
    row = connection.execute(
        "SELECT derivation_owner,goal_kind,goal_local_id "
        "FROM proofir_v3_contract_analysis_derivations WHERE owner_artifact_id=?",
        (result["artifactId"],),
    ).fetchone()
    assert row == (graph["artifactId"], "statement", "statement:goal")
    indexes = {row[1] for row in connection.execute(
        "PRAGMA index_list(proofir_v3_contract_analysis_derivations)")}
    assert "idx_v3_contract_analysis_derivation" in indexes
