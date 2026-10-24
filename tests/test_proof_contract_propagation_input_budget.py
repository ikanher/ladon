"""Aggregate input admission precedes expensive native validation and copying."""

from copy import deepcopy

import pytest
from support.proofir_v3_native import ref
from test_proof_contract_propagation import _contract, _derivation, _step

import ladon.proof_contract_propagation as propagation


def large_inputs():
    source = _contract("large")
    source["extensions"]["example.fixture/v1"]["padding"] = "x" * 4_300_000
    other = deepcopy(source)
    other["producer"]["name"] += "-other"
    # Content hashes deliberately stale: the aggregate cap must run first.
    return _derivation([_step("unused", [], "goal")]), [source, other]


@pytest.mark.parametrize("deadline", [None, "2000-01-01T00:00:00Z"])
def test_aggregate_bytes_stop_before_native_validation_even_when_expired(monkeypatch, deadline):
    graph, sources = large_inputs()

    def forbidden_validation(_value):
        raise AssertionError("aggregate cap must run before native validation")

    monkeypatch.setattr(propagation, "validate_envelope", forbidden_validation)
    result = propagation.propagate_contracts(
        graph, sources, goal_ref=ref("statement", "goal"), rule_bindings=[],
        endpoint_interfaces=[], bounds={} if deadline is None else {"deadlineUtc": deadline},
    )
    assert result["complete"] is False
    assert result["residuals"][0]["code"] == "input-byte-cap"
    assert result["coverage"]["pending"]


def test_cyclic_raw_input_is_rejected_before_native_copy():
    graph = _derivation([_step("unused", [], "goal")])
    graph["extensions"]["example.fixture/v1"]["cycle"] = graph
    with pytest.raises(ValueError):
        propagation.propagate_contracts(
            graph, [], goal_ref=ref("statement", "goal"), rule_bindings=[],
            endpoint_interfaces=[],
        )
