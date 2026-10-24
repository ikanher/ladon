"""Session setup and atomic completion must respect the original deadline."""

import pytest
from test_rational_refinement_session import _count_checks, _goal, _run

from ladon import proof_contract_refinement_session as sessions
from ladon import rational_witness as rational


def test_expired_session_starts_no_round_or_exact_check(tmp_path, monkeypatch):
    calls = _count_checks(monkeypatch)
    monkeypatch.setattr(rational, "_monotonic", lambda: 10.0)
    result = _run(tmp_path)
    assert result["status"] == "deadline-exhausted"
    assert result["roundCount"] == 0
    assert result["candidateChecks"] == 0
    assert result["originalFinding"] is None
    assert result["witnessHistory"] == []
    assert calls == []


def test_final_atomic_family_check_can_complete_at_deadline(tmp_path, monkeypatch):
    calls = _count_checks(monkeypatch)
    monkeypatch.setattr(rational, "_monotonic", lambda: 10.0 if len(calls) >= 4 else 0.0)
    result = _run(tmp_path, goal=_goal(0))
    assert result["status"] == "survived-declared-scope"
    assert result["roundCount"] == 1
    assert result["candidateChecks"] == len(calls) == 4
    assert result["transitionChecks"] == 0
    assert result["originalFinding"] is None


@pytest.mark.parametrize("deadline", [None, True, float("nan"), float("inf"), "10"])
def test_session_requires_a_finite_numeric_absolute_deadline(tmp_path, deadline):
    with pytest.raises(ValueError):
        sessions.run_rational_refinement_session(
            _goal(), {"x": [0]}, [], source_root=tmp_path, finding_id="finding",
            deadline_monotonic=deadline,
        )


def test_no_proposed_refinement_preserves_abstract_outcome(tmp_path, monkeypatch):
    monkeypatch.setattr(rational, "_monotonic", lambda: 0.0)
    result = _run(tmp_path, steps=[])
    assert result["status"] == "abstract-countermodel"
    assert result["roundCount"] == 1
    assert result["originalFinding"]["witness"]["assignment"] == {"x": "0"}
    assert result["transitionChecks"] == 0
