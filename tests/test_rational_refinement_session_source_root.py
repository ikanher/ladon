"""Resolve the source root before any exact work or caller-side cwd change."""

import pytest
from test_rational_refinement_session import _count_checks, _goal, _source_step, _steps

from ladon import proof_contract_refinement_session as sessions
from ladon import rational_witness as rational


@pytest.mark.parametrize("root_kind", ["none", "bool", "missing", "file"])
def test_invalid_source_root_rejects_before_any_check(tmp_path, monkeypatch, root_kind):
    file = tmp_path / "file.txt"
    file.write_text("Not a directory.")
    root = {"none": None, "bool": True, "missing": tmp_path / "missing", "file": file}[root_kind]
    calls = _count_checks(monkeypatch)
    monkeypatch.setattr(rational, "_monotonic", lambda: 0.0)
    with pytest.raises(ValueError):
        sessions.run_rational_refinement_session(
            _goal(), {"x": [0, 1, 2]}, _steps(), source_root=root,
            finding_id="finding", deadline_monotonic=10.0,
        )
    assert calls == []


def test_relative_root_remains_bound_after_caller_changes_directory(tmp_path, monkeypatch):
    _path, steps = _source_step(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(tmp_path)
    original = rational.check_witness

    def change_directory(goal, assignment):
        monkeypatch.chdir(elsewhere)
        return original(goal, assignment)

    monkeypatch.setattr(rational, "check_witness", change_directory)
    monkeypatch.setattr(rational, "_monotonic", lambda: 0.0)
    result = sessions.run_rational_refinement_session(
        _goal(), {"x": [0, 1, 2]}, steps, source_root=".",
        finding_id="finding", deadline_monotonic=10.0,
    )
    assert result["status"] == "abstract-countermodel"
    assert result["roundCount"] == 2
    assert result["rounds"][1]["branch"]["branchKind"] == "source-cited-refinement"
