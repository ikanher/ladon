"""Additional boundary controls for resource correction post180."""

import json

import pytest
from support.proofir_v3_native import ref
from test_proof_contract_propagation import (
    _binding,
    _contract,
    _derivation,
    _interface,
    _run,
    _scope,
    _step,
)

from ladon.proof_contract_propagation import propagate_contracts


def _bytes(result):
    return len(
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )


@pytest.mark.parametrize("cap", [1024, 2048])
def test_maximum_goal_identifier_has_bounded_deadline_result_or_error(cap):
    goal = "é" * 256
    graph = _derivation([_step("unused", [goal], "other")])
    try:
        result = _run(
            graph,
            [],
            goal=goal,
            bindings=[],
            interfaces=[],
            scopes=[],
            bounds={"maxOutputBytes": cap, "deadlineUtc": "2000-01-01T00:00:00Z"},
        )
    except ValueError as error:
        assert cap == 1024
        assert len(str(error)) < 100
    else:
        assert _bytes(result) <= cap
        assert result["complete"] is False


def test_deadline_does_not_waive_raw_input_collection_validation():
    with pytest.raises((TypeError, ValueError)):
        propagate_contracts(
            None,
            [],
            goal_ref=ref("statement", "goal"),
            rule_bindings=None,
            endpoint_interfaces=None,
            bounds={"deadlineUtc": "2000-01-01T00:00:00Z"},
        )


def test_large_raw_bound_key_has_small_error():
    with pytest.raises(ValueError) as error:
        _run({}, [], goal="goal", bindings=[], interfaces=[], scopes=[], bounds={"x" * 100_000: 1})
    assert len(str(error.value)) < 100


def test_repeated_premise_occurrences_are_preflight_charged():
    graph = _derivation([_step("repeat", ["seed"], "goal")])
    # Deliberately invalidate the content hash: preflight must stop before
    # copying/canonicalization rather than rely on later schema rejection.
    graph["payload"]["steps"][0]["premiseRefs"] = [ref("statement", "seed")] * 4096
    result = _run(graph, [], goal="goal", bindings=[], interfaces=[], scopes=[])
    assert result["residuals"][0]["code"] == "graph-reference-cap"
    assert _bytes(result) < 2048


def test_sparse_missing_bindings_have_bounded_diagnostics():
    steps = [_step(f"fan{i}", [f"leaf{i}"], "goal") for i in range(100)]
    result = _run(
        _derivation(steps),
        [],
        goal="goal",
        bindings=[],
        interfaces=[],
        scopes=[],
        bounds={"maxOutputBytes": 4096},
    )
    assert _bytes(result) <= 4096
    assert result["complete"] is False
    assert any(row["code"] == "output-size-cap" for row in result["coverage"]["pending"])
    assert result["residuals"]


def test_byte_limited_witnesses_have_closed_parent_references():
    source = _contract("seed")
    steps = [_step(f"fan{i}", ["seed"], "goal") for i in range(50)]
    result = _run(
        _derivation(steps),
        [source],
        goal="goal",
        bindings=[_binding(step) for step in steps],
        interfaces=[_interface("in", contract=source), _interface("out")],
        scopes=[_scope(source, statement="seed")],
        bounds={"maxOutputBytes": 8192},
    )
    assert result["witnesses"]
    assert _bytes(result) <= 8192
    witnesses = {row["witnessRef"] for row in result["witnesses"]}
    assert all(
        parent in witnesses
        for row in result["witnesses"]
        for parent in row["routeWitness"]["parentWitnessRefs"]
    )
    assert all(
        witness in witnesses
        for frontier in result["frontiers"]
        for contract in frontier["contracts"]
        for witness in contract["routeWitnessRefs"]
    )
