"""Scratch regressions for the falsifier's three task 1.1 counterexamples."""
from datetime import UTC
from datetime import datetime as RealDateTime
from typing import ClassVar

import pytest
from test_proof_contract_backward import _compose_inputs, contract, iface, request

import ladon._proof_contract_obligations_validation as validation
from ladon.proof_contract_obligations import transform_backward_sufficient


def _weaken(*, nested_ref="attributed:nested", interface_ref="attributed:in"):
    interface = iface("in")
    interface["evidenceRefs"] = [interface_ref]
    return request(
        contract(offset=4), "weaken-loss", [interface],
        parameters={"targetOffset": 4, "nestednessRefs": [nested_ref]},
        choices={"weakenLossOffsets": [2]},
    )


def test_request_digest_changes_with_opaque_parameter_and_interface_evidence():
    baseline = transform_backward_sufficient(_weaken())
    changed_parameter = transform_backward_sufficient(
        _weaken(nested_ref="attributed:other-nested")
    )
    changed_interface = transform_backward_sufficient(
        _weaken(interface_ref="attributed:other-interface")
    )
    assert baseline["requestDigest"] != changed_parameter["requestDigest"]
    assert baseline["requestDigest"] != changed_interface["requestDigest"]
    assert baseline["resultDigest"] != changed_parameter["resultDigest"]
    assert baseline["resultDigest"] != changed_interface["resultDigest"]


@pytest.mark.parametrize("rule_id", ["compose", "weaken-loss"])
def test_empty_selected_preimages_are_residual_not_success(rule_id):
    if rule_id == "compose":
        desired, inputs, output = _compose_inputs()
        raw = request(
            desired, rule_id, inputs, output=output,
            parameters={"compositeOperatorId": "operator:composite"},
            choices={"lossSplits": []},
        )
    else:
        raw = request(
            contract(offset=4), rule_id, [iface("in")],
            parameters={"targetOffset": 4, "nestednessRefs": ["attributed:nested"]},
            choices={"weakenLossOffsets": []},
        )
    result = transform_backward_sufficient(raw)
    assert result["status"] == "residual"
    assert result["branches"] == []
    assert result["residuals"]


class _Clock:
    calls = 0
    times: ClassVar[list] = []

    @classmethod
    def now(cls, _zone):
        value = cls.times[min(cls.calls, len(cls.times) - 1)]
        cls.calls += 1
        return value

    @staticmethod
    def fromisoformat(value):
        return RealDateTime.fromisoformat(value)


def _clock(monkeypatch, *values):
    _Clock.calls = 0
    _Clock.times = list(values)
    monkeypatch.setattr(validation, "datetime", _Clock)


def _two_branch_compose():
    desired, inputs, output = _compose_inputs()
    return request(
        desired, "compose", inputs, output=output,
        parameters={"compositeOperatorId": "operator:composite"},
        choices={"lossSplits": [[0, 2], [1, 1]]},
        bounds={"deadlineUtc": "2030-01-01T00:00:00+00:00", "maxBranches": 2},
    )


def test_mid_generation_deadline_preserves_completed_branch_and_pending_count(monkeypatch):
    _clock(monkeypatch,
           RealDateTime(2029, 1, 1, tzinfo=UTC),
           RealDateTime(2031, 1, 1, tzinfo=UTC))
    result = transform_backward_sufficient(_two_branch_compose())
    assert result["status"] == "budget-exhausted"
    assert len(result["branches"]) == 1
    assert result["coverage"]["pendingSplitCount"] == 1
    assert result["residuals"] == [{"code": "deadline", "pendingCount": 1}]


def test_expired_entry_deadline_returns_finite_pending_result(monkeypatch):
    _clock(monkeypatch, RealDateTime(2031, 1, 1, tzinfo=UTC))
    result = transform_backward_sufficient(_two_branch_compose())
    assert result["status"] == "budget-exhausted"
    assert result["branches"] == []
    assert result["coverage"]["pendingSplitCount"] == 2
    assert result["residuals"] == [{"code": "deadline", "pendingCount": 2}]
