"""Resource stops retain completed work even in the final requested round."""

import pytest
from test_rational_refinement_session import _count_checks, _goal, _run, _steps
from test_rational_witness_session_v5 import _three_variable_goal

from ladon import proof_contract_refinement_session as sessions
from ladon import rational_witness as rational


def test_final_round_reports_deadline_if_minimization_cannot_start(tmp_path, monkeypatch):
    calls = _count_checks(monkeypatch)
    monkeypatch.setattr(rational, "_monotonic", lambda: 10.0 if calls else 0.0)
    result = _run(tmp_path, steps=[])
    assert result["status"] == "deadline-exhausted"
    assert result["witnessHistory"][0]["assignment"] == {"x": "0"}
    assert result["minimizationRechecks"] == 0


def test_later_witness_survives_expiry_before_its_minimization(tmp_path, monkeypatch):
    calls = _count_checks(monkeypatch)
    monkeypatch.setattr(rational, "_monotonic", lambda: 10.0 if len(calls) >= 5 else 0.0)
    result = _run(tmp_path)
    assert result["status"] == "deadline-exhausted"
    assert result["candidateChecks"] == 3
    assert [w["assignment"] for w in result["witnessHistory"]] == [{"x": "0"}, {"x": "1"}]


def test_completed_transition_is_counted_and_retained_at_deadline(tmp_path, monkeypatch):
    calls = _count_checks(monkeypatch)
    monkeypatch.setattr(rational, "_monotonic", lambda: 10.0 if len(calls) >= 3 else 0.0)
    result = _run(tmp_path)
    assert result["status"] == "deadline-exhausted"
    assert result["roundCount"] == 1
    assert result["transitionChecks"] == 1
    assert result["rounds"][-1]["pendingBranchCheck"]["witnessCheck"]["status"] == "outside-assumptions"


def test_final_round_reduction_exhaustion_remains_visible(tmp_path, monkeypatch):
    monkeypatch.setattr(rational, "_monotonic", lambda: 0.0)
    result = sessions.run_rational_refinement_session(
        _three_variable_goal(), {"x": [0, 1], "y": [0, 1], "z": [0, 1]}, [],
        source_root=tmp_path, finding_id="finding", deadline_monotonic=10.0,
        max_reductions=1,
    )
    assert result["status"] == "budget-exhausted"
    assert result["stopReason"] == "reduction-cap"
    assert result["reductionAttempts"] == 1
    assert result["rounds"][0]["minimization"]["minimality"] is False
    assert result["witnessHistory"][0]["assignment"] == {"x": "1", "y": "1", "z": "1"}


class CustomMapping(dict):
    """Must not be normalized into trusted JSON-native input."""


def test_nested_non_native_input_is_rejected_before_work(tmp_path, monkeypatch):
    calls = _count_checks(monkeypatch)
    monkeypatch.setattr(rational, "_monotonic", lambda: 0.0)
    steps = _steps()
    steps[0][0] = CustomMapping(steps[0][0])
    with pytest.raises(ValueError):
        _run(tmp_path, steps=steps)
    assert calls == []


def test_finding_name_uses_the_existing_utf8_byte_bound(tmp_path, monkeypatch):
    calls = _count_checks(monkeypatch)
    monkeypatch.setattr(rational, "_monotonic", lambda: 0.0)
    with pytest.raises(ValueError):
        sessions.run_rational_refinement_session(
            _goal(), {"x": [0]}, [], source_root=tmp_path, finding_id="χ" * 100,
            deadline_monotonic=10.0,
        )
    assert calls == []
