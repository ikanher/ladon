"""Concrete independent audit cases retain bounded, attributable known support."""

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


def test_expired_deadline_does_not_waive_goal_reference_bounds():
    with pytest.raises((TypeError, ValueError)):
        propagate_contracts(
            None, None, goal_ref=ref("statement", "a" * (9 * 1024**2)),
            rule_bindings=None, endpoint_interfaces=None, scope_bindings=None,
            bounds={"deadlineUtc": "2000-01-01T00:00:00Z"},
        )


def test_deeper_partial_visit_retains_known_shallower_frontier():
    source = _contract("seed")
    steps = [_step("a-shallow", ["statement:x"], "statement:goal"),
             _step("z-deep", ["statement:middle"], "statement:goal"),
             _step("middle", ["statement:x"], "statement:middle"),
             _step("x", ["statement:seed"], "statement:x")]
    result = _run(
        _derivation(steps), [source], goal="statement:goal",
        bindings=[_binding(step) for step in steps],
        interfaces=[_interface("in", contract=source), _interface("out")],
        scopes=[_scope(source, statement="statement:seed")], bounds={"maxDepth": 2},
    )
    frontiers = {row["statementRef"]["localId"]: row["contracts"]
                 for row in result["frontiers"]}
    assert frontiers["statement:goal"]
    assert frontiers["statement:x"]
    assert result["status"] == "partial"
    assert any(row["code"] == "depth-cap" for row in result["coverage"]["pending"])


def test_output_budget_retains_fitted_witnesses_before_serializing_large_result(monkeypatch):
    import ladon.proof_contract_propagation as propagation

    source = _contract("seed")
    steps = [_step(f"fan-{i}", ["statement:seed"], "statement:goal") for i in range(70)]
    evidence = [ref("check-run", f"check:large-{i}") for i in range(100)]
    interface = _interface("same", contract=source)
    interface["evidenceRefs"] = evidence
    original = propagation._canonical
    serialized_sizes = []

    def measured(value):
        encoded = original(value)
        serialized_sizes.append(len(encoded))
        return encoded

    monkeypatch.setattr(propagation, "_canonical", measured)
    result = _run(
        _derivation(steps, evidence), [source], goal="statement:goal",
        bindings=[_binding(step, output_interface="same") for step in steps],
        interfaces=[interface], scopes=[_scope(source, statement="statement:seed")],
        bounds={"maxOutputBytes": 64 * 1024},
    )
    assert result["witnesses"]
    assert any(row["contracts"] for row in result["frontiers"])
    assert len(json.dumps(result, separators=(",", ":")).encode()) <= 64 * 1024
    assert max(serialized_sizes, default=0) <= 64 * 1024
