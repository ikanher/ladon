"""Malformed source-goal data cannot bypass atomic construction boundaries."""

import copy
import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def api():
    return importlib.import_module("ladon.proof_contract_source_obligations")


@pytest.fixture
def capture():
    path = Path(__file__).parent / "fixtures/proof_contract_source_obligations/closed-goal.json"
    return json.loads(path.read_text())


def _expected():
    return {"kind": "forallNat2", "leftOperator": "ObligationsRed.N2",
            "map": "ObligationsRed.F2", "constantName": "ObligationsRed.C",
            "inputScale": "ObligationsRed.N1", "offset": 1}


def _change_node(capture, tag, replacement):
    value = json.loads(capture["goal"]["typeStructural"].split(":", 1)[1])
    row = next(node for node in value["nodes"] if node[0] == tag)
    row[:] = replacement
    capture["goal"]["typeStructural"] = "ladon-expr-dag-v1:" + json.dumps(value)


def test_actual_structural_goal_is_accepted_despite_unrelated_display(api, capture):
    api._validate_captured_requirement(capture, _expected())


@pytest.mark.parametrize("role,value", [
    ("leftOperator", "ObligationsRed.N1"), ("map", "ObligationsRed.N2"),
    ("constantName", "ObligationsRed.D"), ("inputScale", "ObligationsRed.N2"),
    ("offset", 2),
])
def test_exact_roles_cannot_be_exchanged_or_weakened(api, capture, role, value):
    expected = _expected()
    expected[role] = value
    with pytest.raises((ValueError, TypeError)):
        api._validate_captured_requirement(capture, expected)


@pytest.mark.parametrize("node", [
    ["lit", "Lean.Literal.natVal -1"],
    ["lit", "Lean.Literal.natVal ignored 1"],
    ["lit", "Lean.Literal.natVal " + "9" * 5000],
])
def test_nat_representation_is_strict_and_bounded(api, capture, node):
    _change_node(capture, "lit", node)
    with pytest.raises((ValueError, TypeError)):
        api._validate_captured_requirement(capture, _expected())


def test_malformed_name_representation_cannot_be_interpreted_as_lean_syntax(api, capture):
    _change_node(capture, "const", ["const", "`Nat\naxiom smuggled : False", "[]"])
    with pytest.raises((ValueError, TypeError)):
        api._validate_captured_requirement(capture, _expected())


def test_historical_opaque_text_is_not_a_structural_goal(api, capture):
    capture["goal"]["typeStructural"] = "∀ s x, N2 s (F2 x) ≤ C * N1 (s+1) x"
    with pytest.raises((ValueError, TypeError)):
        api._validate_captured_requirement(capture, _expected())


def test_free_hypothesis_is_not_a_closed_goal(api, capture):
    _change_node(capture, "bvar", ["fvar", "`missingProof"])
    with pytest.raises((ValueError, TypeError)):
        api._validate_captured_requirement(capture, _expected())


def _invalid_request():
    return {
        "repoRoot": Path.cwd(), "parentSnapshot": {}, "providerSnapshot": {},
        "parentReadingId": "parent", "providerReadingId": "provider",
        "desiredReadingId": "desired", "backwardRequest": None,
        "backwardResult": {}, "branchIndex": 0, "premiseOrdinal": 0,
        "deadlineMonotonic": 10**20,
        "limits": {"timeout_seconds": 30, "max_output_bytes": 8 * 1024**2,
                   "max_rss_bytes": 12 * 1024**3},
    }


def test_oversized_reading_is_not_echoed_into_a_large_rejection(api):
    request = _invalid_request()
    request["parentReadingId"] = "x" * (9 * 1024**2)
    result = api.instantiate_source_bound_premise(request)
    assert result["status"] == "rejected"
    assert len(json.dumps(result).encode()) < 4096


def test_cyclic_input_is_a_bounded_rejection(api):
    request = _invalid_request()
    cyclic = {}
    cyclic["again"] = cyclic
    request["parentSnapshot"] = cyclic
    result = api.instantiate_source_bound_premise(request)
    assert result["status"] == "rejected"
    assert len(json.dumps(result).encode()) < 4096


def test_deep_input_is_a_bounded_rejection(api):
    request = _invalid_request()
    nested = {}
    for _ in range(1500):
        nested = {"again": nested}
    request["parentSnapshot"] = nested
    result = api.instantiate_source_bound_premise(request)
    assert result["status"] == "rejected"
    assert len(json.dumps(result).encode()) < 4096


def test_target_validation_preserves_the_supplied_capture(api, capture):
    before = copy.deepcopy(capture)
    api._validate_captured_requirement(capture, _expected())
    assert capture == before
