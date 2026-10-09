"""Real original-context application and independent compiler controls."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from ladon.lean_toolchain import resolve_toolchain_context
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

pytestmark = pytest.mark.skipif(shutil.which("lean") is None, reason="Lean unavailable")
FIXTURE = Path(__file__).parent / "fixtures/lean_integration"


def _capture(tmp_path, text, line, column):
    prefix = subprocess.run(
        ["lean", "--print-prefix"], cwd=FIXTURE, capture_output=True,
        text=True, check=True, timeout=15,
    ).stdout.strip()
    lean = Path(prefix) / "bin/lean"
    (tmp_path / "lean-toolchain").write_bytes((FIXTURE / "lean-toolchain").read_bytes())
    source = tmp_path / "Owner.lean"
    source.write_text(text)
    context = resolve_toolchain_context(
        tmp_path, lean_path=lean, lake_path=lean.with_name("lake"), selection_mode="explicit",
    )
    captured = capture_source_goal(SourceGoalCaptureRequest(
        repo_root=tmp_path, source_path="Owner.lean", module="Owner",
        line=line, column=column, toolchain=context, timeout_seconds=30,
    ))
    assert captured["status"] == "captured", captured
    return source, context, captured["capture"]


def _value_context(tmp_path, value="h"):
    text = (
        "namespace Owner\n"
        "variable {α : Type} [Inhabited α]\n"
        "example (x : α) (h : x = x) : x = x := by\n"
        f"  have z : x = x := {value}\n"
        "  skip\n"
        "end Owner\n"
    )
    return _capture(tmp_path, text, 5, 6)


def _request(root, context, capture, term):
    return SourceGoalCompletionRequest(
        repo_root=root, capture=capture, term=term, toolchain=context, timeout_seconds=30,
    )


def _assert_completed(result, capture):
    assert result["status"] == "completed", result
    assert result["captureId"] == capture["captureId"]
    assert result["application"]["originalGoal"]["typeStructural"] == capture["goal"]["typeStructural"]
    assert result["replay"]["status"] == "accepted"
    assert result["trust"]["coverage"] == "complete"
    assert result["trust"]["accepted"] is True


def test_real_local_value_application_replays_and_keeps_project_unchanged(tmp_path):
    _source, context, capture = _value_context(tmp_path)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = complete_source_goal(_request(tmp_path, context, capture, "z"))
    _assert_completed(result, capture)
    assert result["trust"]["observedAxioms"] == []
    assert "let" in result["replay"]["generatedSource"]
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before


def test_real_residual_and_wrong_term_do_not_replay(tmp_path):
    _source, context, capture = _value_context(tmp_path)
    request = _request(tmp_path, context, capture, "?_")
    partial = complete_source_goal(request)
    assert partial["status"] == "incomplete", partial
    residual = partial["application"]["residualGoals"][0]
    assert residual["typeStructural"] == capture["goal"]["typeStructural"]
    assert residual["localContext"] == capture["goal"]["localContext"]
    assert partial["replay"]["status"] == "not-run"
    wrong = complete_source_goal(replace(request, term="Nat.zero"))
    assert wrong["status"] == "rejected", wrong
    assert wrong["replay"]["status"] == "not-run"


def test_real_admitted_local_value_is_visible_to_independent_trust_check(tmp_path):
    _source, context, capture = _value_context(tmp_path, "sorry")
    result = complete_source_goal(_request(tmp_path, context, capture, "z"))
    assert result["status"] == "trust-rejected", result
    assert result["replay"]["status"] == "accepted"
    assert result["trust"]["coverage"] == "complete"
    assert "sorryAx" in result["trust"]["observedAxioms"]
    assert result["trust"]["accepted"] is False


def test_real_allowed_classical_axiom_is_reported_as_foundational(tmp_path):
    text = "example (p : Prop) : p ∨ ¬p := by\n  skip\n"
    _source, context, capture = _capture(tmp_path, text, 2, 6)
    result = complete_source_goal(_request(tmp_path, context, capture, "Classical.em p"))
    _assert_completed(result, capture)
    assert "Classical.choice" in result["trust"]["observedAxioms"]


def test_source_local_uncompiled_dependency_receives_independent_replay_coverage(tmp_path):
    text = "def localWitness : True := True.intro\nexample : True := by\n  skip\n"
    _source, context, capture = _capture(tmp_path, text, 3, 6)
    result = complete_source_goal(_request(tmp_path, context, capture, "localWitness"))
    _assert_completed(result, capture)
    assert result["trust"]["observedAxioms"] == []
    assert result["replay"]["sourceContext"]["basis"] == "selected-source-environment"
