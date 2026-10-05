"""Real Lean fixture for ordered, dependent source-goal capture."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

FIXTURE = next(
    parent / "tests" / "fixtures" / "lean_integration"
    for parent in Path(__file__).resolve().parents
    if (parent / "tests" / "fixtures" / "lean_integration" / "lean-toolchain").is_file()
)


def _lean_binary() -> Path:
    prefix = subprocess.run(
        ["lean", "--print-prefix"], cwd=FIXTURE, capture_output=True,
        text=True, check=True, timeout=15,
    ).stdout.strip()
    return Path(prefix) / "bin" / "lean"


def _fixture(tmp_path: Path, *, unfinished=False):
    from ladon.lean_toolchain import resolve_toolchain_context

    lean = _lean_binary()
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy2(FIXTURE / "lean-toolchain", repo / "lean-toolchain")
    source = repo / "Owner.lean"
    text = (
        "namespace Owner\n"
        "variable (α : Type) (x : α)\n"
        'local notation "Point" => α\n'
        "example (h : x = x) : (x = x) ∧ (x = x) := by\n"
        "  let y : Point := x\n"
        "  constructor\n"
        "  · skip\n"
        "    exact h\n"
        "  · skip\n"
        "    exact h\n"
        "end Owner\n"
    )
    if unfinished:
        text = text.replace("    exact h\n", "")
    source.write_text(text, encoding="utf-8")
    context = resolve_toolchain_context(
        repo,
        lake_path=lean.with_name("lake"),
        lean_path=lean,
        selection_mode="explicit",
    )
    return repo, source, text, context


@pytest.mark.skipif(shutil.which("lean") is None, reason="Lean toolchain unavailable")
def test_real_source_capture_selects_ordered_goals_and_preserves_locals(tmp_path: Path):
    from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal

    repo, source, original, context = _fixture(tmp_path)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    repo_before = {path.relative_to(repo): path.read_bytes() for path in repo.rglob("*") if path.is_file()}
    line = 6
    column = 13

    def capture(ordinal):
        request = SourceGoalCaptureRequest(
            repo_root=repo,
            source_path="Owner.lean",
            module="Owner",
            line=line,
            column=column,
            toolchain=context,
            goal_ordinal=ordinal,
            timeout_seconds=45,
            max_rss_bytes=8 * 1024**3,
        )
        return capture_source_goal(request)

    ambiguous = capture(None)
    assert ambiguous["status"] == "ambiguous", ambiguous
    assert ambiguous["capture"] is None

    first, second = capture(0), capture(1)
    assert first["status"] == second["status"] == "captured", (first, second)
    a, b = first["capture"], second["capture"]
    _assert_selection(a, b, original, before, line, column)
    _assert_locals(a)
    _assert_environment(a, context)
    assert source.read_text(encoding="utf-8") == original
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    assert {path.relative_to(repo): path.read_bytes() for path in repo.rglob("*") if path.is_file()} == repo_before


def _assert_selection(a, b, original, before, line, column):
    assert a["goal"]["goalCount"] == b["goal"]["goalCount"] == 2
    assert a["goal"]["ordinal"] == 0 and b["goal"]["ordinal"] == 1
    assert a["goal"]["goalId"] != b["goal"]["goalId"]
    assert a["source"]["digest"] == "sha256:" + before
    assert a["source"]["position"] == {
        "line": line, "column": column,
        "byteOffset": len(original[:original.index("  constructor") + len("  constructor")].encode()),
    }
    assert a["source"]["syntaxRange"]["startByte"] < a["source"]["syntaxRange"]["endByte"]



def _assert_locals(capture):
    rows = capture["goal"]["localContext"]
    visible = [row for row in rows if not row["implementationDetail"]]
    visible_names = [row["userName"] for row in visible]
    named_positions = [visible_names.index(name) for name in ("α", "x", "h", "y")]
    assert named_positions == sorted(named_positions)
    _assert_local_values(rows, visible)


def _assert_local_values(rows, visible):
    _assert_internal_roles(rows)
    y = next(row for row in visible if row["userName"] == "y")
    assert y["valueDisplay"]
    assert y["valueStructural"]
    x = next(row for row in visible if row["userName"] == "x")
    assert x["localId"] in y["dependencies"]


def _assert_environment(capture, context):
    assert capture["environment"]["executionContextRef"] == context.context_identity
    assert capture["environment"]["leanVersion"]
    assert capture["environment"]["executableDigest"] == context.lean_identity
    assert capture["environment"]["compiledInventory"]
    assert capture["environment"]["namespace"]
    assert "openDeclarationsStructural" in capture["environment"]
    assert "optionsStructural" in capture["environment"]
    assert capture["captureId"]


@pytest.mark.skipif(shutil.which("lean") is None, reason="Lean toolchain unavailable")
def test_unfinished_source_and_stale_or_invalid_positions_are_reported(tmp_path: Path):
    from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal

    repo, source, _, context = _fixture(tmp_path, unfinished=True)
    original = source.read_bytes()
    repo_before = {path.relative_to(repo): path.read_bytes() for path in repo.rglob("*") if path.is_file()}
    request = SourceGoalCaptureRequest(
        repo_root=repo, source_path="Owner.lean", module="Owner",
        line=7, column=8, toolchain=context, goal_ordinal=0,
        timeout_seconds=45, max_rss_bytes=8 * 1024**3,
    )
    invalid = capture_source_goal(
        replace(request, line=99)
    )
    _assert_failure(invalid, "unavailable")

    stale = capture_source_goal(replace(request, expected_source_digest="sha256:" + "0" * 64))
    _assert_failure(stale, "stale")

    # Capture does not complete or rewrite the user's unfinished proof.
    captured = capture_source_goal(request)
    assert captured["status"] == "captured", captured
    assert captured["capture"]["goal"]["goalCount"] == 1
    prefix = original.decode().splitlines(keepends=True)
    expected_offset = len(("".join(prefix[:6]) + prefix[6][:8]).encode())
    assert captured["capture"]["source"]["position"]["byteOffset"] == expected_offset
    assert source.read_bytes() == original
    assert {path.relative_to(repo): path.read_bytes() for path in repo.rglob("*") if path.is_file()} == repo_before


def _assert_failure(result, status):
    assert result["status"] == status
    assert result["capture"] is None


def _assert_internal_roles(rows):
    assert all(row["localId"] for row in rows)
    assert all("implementationDetail" in row for row in rows)
    assert any(row["implementationDetail"] for row in rows)
