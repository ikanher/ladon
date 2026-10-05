"""Compiler fragments remain caller evidence; CLI capture preserves source context."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ladon.proof_search_cli import proof_search_main

FIXTURE = next(
    parent / "tests" / "fixtures" / "lean_integration"
    for parent in Path(__file__).resolve().parents
    if (parent / "tests" / "fixtures" / "lean_integration" / "lean-toolchain").is_file()
)


def test_parser_keeps_supplied_type_mismatch_separate_from_source_observation():
    from ladon.compiler_goal_query import parse_compiler_goal_query

    # Lean plain formatter uses a 1-based line and already-0-based scalar column.
    stream = (
        "Owner.lean:3:28: error: Type mismatch\n"
        "  True\n"
        "has type\n"
        "  Prop\n"
        "but is expected to have type\n"
        "  Nat\n"
    )
    result = parse_compiler_goal_query(stream)
    assert result["schema"] == "ladon-compiler-goal-query-v1"
    assert result["status"] == "parsed"
    assert result["evidenceBasis"] == "caller-supplied-compiler-text"
    assert result["inputDigest"] == "sha256:" + hashlib.sha256(stream.encode("utf-8")).hexdigest()
    assert result["recordCount"] == 1
    assert result["selected"] == {
        "ordinal": 0, "file": "Owner.lean", "line": 3, "column": 28,
        "expression": "True", "actualType": "Prop", "expectedType": "Nat",
    }
    assert result["diagnostic"] is None


def test_parser_requires_explicit_ordinal_for_multiple_relevant_records():
    from ladon.compiler_goal_query import parse_compiler_goal_query

    one = "Owner.lean:3:28: error: Type mismatch\n  True\nhas type\n  Prop\nbut is expected to have type\n  Nat\n"
    two = "Owner.lean:9:0: error: Type mismatch\n  other\nhas type\n  String\nbut is expected to have type\n  Nat\n"
    result = parse_compiler_goal_query(one + two)
    assert result["status"] == "ambiguous"
    assert result["recordCount"] == 2
    assert result["selected"] is None
    assert result["diagnostic"]["code"]
    selected = parse_compiler_goal_query(one + two, diagnostic_ordinal=1)
    assert selected["status"] == "parsed"
    assert selected["selected"]["ordinal"] == 1
    assert selected["selected"]["line"] == 9
    assert selected["selected"]["expectedType"] == "Nat"


def test_parser_fails_closed_on_no_or_unsupported_diagnostic():
    from ladon.compiler_goal_query import parse_compiler_goal_query

    no_match = parse_compiler_goal_query("Owner.lean:2:1: error: unknown identifier 'x'\n")
    assert no_match["status"] == "unsupported"
    assert no_match["recordCount"] == 0
    assert no_match["selected"] is None
    assert no_match["diagnostic"]["code"]
    malformed = parse_compiler_goal_query(
        "Owner.lean:7:3: error: Type mismatch\n  value\n"
    )
    assert malformed["status"] == "unsupported"
    assert malformed["selected"] is None
    assert malformed["diagnostic"]["code"]


def _lean_context(repo: Path):
    from ladon.lean_toolchain import resolve_toolchain_context

    prefix = subprocess.run(
        ["lean", "--print-prefix"], cwd=FIXTURE, capture_output=True,
        text=True, check=True, timeout=15,
    ).stdout.strip()
    lean = Path(prefix) / "bin" / "lean"
    return resolve_toolchain_context(
        repo, lean_path=lean, lake_path=lean.with_name("lake"),
        selection_mode="explicit",
    )


@pytest.mark.skipif(shutil.which("lean") is None, reason="Lean toolchain unavailable")
def test_public_cli_captures_nested_section_goal_with_source_options_and_unicode(tmp_path, capsys):
    """One real CLI round trip checks source selection and exact contextual evidence."""
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy2(FIXTURE / "lean-toolchain", repo / "lean-toolchain")
    source_text = (
        "namespace Owner\n"
        "section Inner\n"
        "open Nat\n"
        'local notation "Point" => Nat\n'
        "set_option pp.universes true in\n"
        "example (α : Type) (x : α) (same : x = x) : x = x := by\n"
        "  let dependent : α := x\n"
        "  skip\n"
        "end Inner\n"
        "end Owner\n"
    )
    (repo / "Owner.lean").write_text(source_text, encoding="utf-8")
    # `skip` is a syntax position inside the tactic with an active goal.
    line, column = 8, 6
    status = proof_search_main([
        "goal", "capture", "--repo-root", str(repo), "--source", "Owner.lean",
        "--module", "Owner", "--line", str(line), "--column", str(column),
        "--lean-path", str(_lean_context(repo).lean_path),
        "--lake-path", str(_lean_context(repo).lake_path),
        "--format", "json",
    ])
    captured = capsys.readouterr()
    assert status == 0, captured.err
    payload = json.loads(captured.out)
    assert payload["status"] == "captured"
    _assert_source_binding(payload, repo, source_text)
    _assert_nested_scope(payload)
    _assert_nested_locals(payload)


def _assert_source_binding(payload, repo, source_text):
    assert payload["capture"]["source"]["path"] == "Owner.lean"
    assert payload["capture"]["source"]["digest"] == "sha256:" + hashlib.sha256(
        (repo / "Owner.lean").read_bytes()
    ).hexdigest()
    assert (repo / "Owner.lean").read_text() == source_text


def _assert_nested_scope(payload):
    assert payload["capture"]["environment"]["namespace"]
    assert "pp.universes" in payload["capture"]["environment"]["optionsStructural"]
    assert payload["capture"]["environment"]["openDeclarationsStructural"]
    assert payload["capture"]["replay"] == "not-run"


def _assert_nested_locals(payload):
    rows = payload["capture"]["goal"]["localContext"]
    visible = [row for row in rows if not row["implementationDetail"]]
    assert [row["userName"] for row in visible] == ["α", "x", "same", "dependent"]
    dependent = visible[-1]
    assert dependent["valueDisplay"] == "x"
    assert visible[1]["localId"] in dependent["dependencies"]


def test_diagnostic_cli_retains_caller_fragments_when_capture_is_unavailable(
    monkeypatch, tmp_path, capsys,
):
    """Caller-supplied compiler fragments survive a genuine capture failure."""
    import ladon.proof_search_goal_cli as goal_cli

    def unavailable(_request):
        return {
            "schema": "ladon-source-goal-capture-result-v1",
            "operation": "capture-source-goal", "status": "unavailable",
            "capture": None,
            "diagnostic": {"code": "no-tactic-info", "message": "no goal at location"},
        }

    monkeypatch.setattr(goal_cli, "capture_source_goal", unavailable)
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy2(FIXTURE / "lean-toolchain", repo / "lean-toolchain")
    (repo / "Owner.lean").write_text("example : True := by trivial\n", encoding="utf-8")
    context = _lean_context(repo)
    diagnostic = tmp_path / "lean.stderr"
    diagnostic.write_text(
        "Owner.lean:7:3: error: Type mismatch\n  value\nhas type\n  Nat\nbut is expected to have type\n  Bool\n",
        encoding="utf-8",
    )
    status = proof_search_main([
        "goal", "diagnostic", "--repo-root", str(repo),
        "--diagnostic-file", str(diagnostic), "--module", "Owner",
        "--lean-path", str(context.lean_path), "--lake-path", str(context.lake_path),
        "--format", "json",
    ])
    captured = capsys.readouterr()
    assert status == 1
    payload = json.loads(captured.out)
    assert payload["status"] == "unavailable"
    assert payload["queryEvidence"]["selected"]["expectedType"] == "Bool"
    assert payload["captureResult"]["status"] == "unavailable"
    assert payload["captureResult"]["capture"] is None
    assert payload.get("capture") is None
    assert payload["queryEvidence"]["selected"] != payload["captureResult"].get("goal")


def test_source_capture_route_rejects_handwritten_goal_argument_as_invocation(capsys):
    status = proof_search_main(["goal", "capture", "--goal", "True"])
    captured = capsys.readouterr()
    assert status == 2
    assert captured.out == ""
    terminal = json.loads(captured.err)
    assert terminal["exitClass"] == "invocation"
    assert terminal["exitCode"] == 2


@pytest.mark.parametrize("ordinal", [-1, True])
def test_diagnostic_ordinal_requires_nonnegative_integer(ordinal):
    from ladon.compiler_goal_query import parse_compiler_goal_query

    with pytest.raises(ValueError):
        parse_compiler_goal_query("", diagnostic_ordinal=ordinal)
