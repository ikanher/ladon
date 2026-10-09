"""Public completion workflow tests with explicitly scripted observer frames.

These fixtures exercise orchestration and frame binding only. They are not Lean
execution, proof, replay, or trust evidence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from ladon.process_supervisor import ProcessResult

SOURCE_FRAME = "LADON_GOAL_FRAME "
COMPLETION_FRAME = "LADON_COMPLETION_FRAME "
REPLAY_FRAME = "LADON_COMPLETION_REPLAY "
SOURCE = "example: True := by\n  skip\n"


def _fixture(tmp_path: Path, monkeypatch):
    from ladon.lean_toolchain import LeanToolchainContext, _identity, _source_tree_identity
    from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "lean-toolchain").write_text("leanprover/lean4:v4.32.1\n", encoding="utf-8")
    source_path = repo / "Owner.lean"
    source_path.write_text(SOURCE, encoding="utf-8")
    pin = "leanprover/lean4:v4.32.1"
    binaries = tmp_path / "toolchain"
    binaries.mkdir()
    lean, lake = binaries / "lean", binaries / "lake"
    lean.write_bytes(b"scripted lean identity")
    lake.write_bytes(b"scripted lake identity")
    compiled_root = repo / ".lake/build/lib/lean"
    compiled_root.mkdir(parents=True)
    prelude = compiled_root / "Init.olean"
    prelude.write_bytes(b"scripted compiled Init identity")
    environment = {"LEAN_PATH": str(compiled_root)}
    context = LeanToolchainContext(
        repo_root=repo, lake_path=lake, lean_path=lean,
        pin_content=pin, pin_digest=_digest(pin.encode()),
        lake_identity=_identity(lake), lean_identity=_identity(lean),
        source_tree_identity=_source_tree_identity(repo, None),
        lean_release="4.32.1", lean_commit="fixture-commit",
        selection_mode="explicit", environment_keys=("LEAN_PATH",),
        environment=environment, library_roots=(compiled_root,),
    )
    request = SourceGoalCaptureRequest(
        repo_root=repo, source_path="Owner.lean", module="Owner", line=2,
        column=6, toolchain=context,
    )
    return repo, source_path, context, request, capture_source_goal


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _source_observation(payload: dict[str, Any], context) -> str:
    source = SOURCE.encode()
    frame = {
        "frame": "LADON_GOAL_FRAME",
        "protocolVersion": "ladon-lean-source-goal-v1/capture",
        "helperVersion": "ladon-source-goal-helper-v1",
        "leanVersion": context.lean_release, "leanCommit": context.lean_commit,
        "leanExecutablePath": str(context.lean_path),
        "compiledModulePaths": [{
            "module": "Init", "path": str(context.library_roots[0] / "Init.olean"),
        }],
        "requestId": payload["requestId"], "contextRef": payload["contextRef"],
        "module": payload["module"], "filename": payload["filename"],
        "sourceDigest": payload["sourceDigest"], "line": payload["line"],
        "column": payload["column"], "byteOffset": 26,
        "goals": [{
            "goalId": "_uniq.1", "typeDisplay": "True",
            "typeStructural": "Lean.Expr.const `True []", "localContext": [],
        }],
        "goalCount": 1, "useAfter": False, "rangeStartByte": 22,
        "rangeEndByte": 26, "selectionEndByte": 26, "namespaceName": "Owner",
        "openDeclarationsStructural": "[]", "optionsStructural": "[]",
        "importedModules": ["Init"], "observationCount": 1,
    }
    assert payload["sourceDigest"] == _digest(source)
    return SOURCE_FRAME + json.dumps(frame, sort_keys=True)


def _valid_capture(context, source_path: Path, capture_source_goal, request):
    calls: list[tuple[str, dict[str, Any]]] = []

    def runner(command, **options):
        payload = json.loads(options["input_bytes"].decode().split(" ", 1)[1])
        calls.append(("capture", payload))
        return ProcessResult(tuple(command), 0, _source_observation(payload, context), "", 0.01, peak_rss_bytes=1024)

    result = capture_source_goal(request, runner=runner)
    assert result["status"] == "captured", result
    assert len(calls) == 2
    return result["capture"]


def _completion_frame(
    request: dict[str, Any], context, *, status="accepted", goal_id="_uniq.1",
) -> str:
    init_path = context.library_roots[0] / "Init.olean"
    context_module = "LadonCompletionContext_" + request["requestId"] if status == "accepted" else ""
    if context_module:
        Path(request["snapshotPath"]).with_name(context_module + ".olean").write_bytes(b"scripted private source environment")
    frame = {
        "frame": "LADON_COMPLETION_FRAME",
        "protocolVersion": "ladon-lean-source-completion-v1/check",
        "helperVersion": "ladon-source-completion-helper-v2",
        "requestId": request["requestId"], "captureId": request["captureId"],
        "termDigest": request["termDigest"], "contextRef": request["contextRef"],
        "module": request["module"], "filename": request["filename"],
        "sourceDigest": request["sourceDigest"], "line": request["line"],
        "column": request["column"], "leanVersion": context.lean_release,
        "leanCommit": context.lean_commit, "leanExecutablePath": str(context.lean_path),
        "goalOrdinal": request["goalOrdinal"], "goalCount": 1, "useAfter": False,
        "byteOffset": 26, "rangeStartByte": 22, "rangeEndByte": 26,
        "selectionEndByte": 26, "namespaceName": "Owner",
        "openDeclarationsStructural": "[]", "optionsStructural": "[]",
        "importedModules": ["Init"], "compiledModulePaths": [{
            "module": "Init", "path": str(init_path),
        }], "directImports": [], "sourceContextModule": context_module,
        "selectedGoal": {
            "goalId": goal_id, "typeDisplay": "True",
            "typeStructural": "Lean.Expr.const `True []", "localContext": [],
        },
        "status": status, "termDisplay": "True.intro",
        "termStructural": "Lean.Expr.const `True.intro []",
        "residualGoals": [],
        "closedTargetText": "True", "closedProofText": "True.intro",
        "diagnostic": None,
    }
    if status != "accepted":
        frame["closedTargetText"] = ""
        frame["closedProofText"] = ""
        if status == "incomplete":
            frame["residualGoals"] = [{
                "goalId": "_uniq.residual", "typeDisplay": "True",
                "typeStructural": "Lean.Expr.const `True []", "localContext": [],
            }]
    return COMPLETION_FRAME + json.dumps(frame, sort_keys=True)


def _replay_frame(expected: dict[str, Any], *, axioms=None, coverage="complete") -> str:
    frame = {
        "frame": "LADON_COMPLETION_REPLAY",
        "protocolVersion": "ladon-lean-source-completion-replay-v1",
        **expected,
        "observedAxioms": None if coverage != "complete" else (axioms or []),
        "coverage": coverage,
    }
    return REPLAY_FRAME + json.dumps(frame, sort_keys=True)


def _workflow(
    tmp_path, monkeypatch, *, application_status="accepted", axioms=None,
    coverage="complete", duplicate_application=False, goal_id="_uniq.1",
    missing_replay=False, application_limit=None,
):
    repo, source_path, context, capture_request, capture_source_goal = _fixture(tmp_path, monkeypatch)
    capture = _valid_capture(context, source_path, capture_source_goal, capture_request)
    from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

    request = SourceGoalCompletionRequest(
        repo_root=repo, capture=capture, term="True.intro", toolchain=context,
    )
    sequence: list[tuple[str, dict[str, Any]]] = []

    def runner(command, **options):
        assert options["timeout_seconds"] == request.timeout_seconds
        assert options["max_output_bytes"] == request.max_output_bytes
        assert options["max_rss_bytes"] == request.max_rss_bytes
        payload_bytes = options["input_bytes"]
        text = payload_bytes.decode()
        if text.startswith("LADON_GOAL_REQUEST "):
            payload = json.loads(text.split(" ", 1)[1])
            sequence.append(("capture", payload))
            output = _source_observation(payload, context)
        elif text.startswith("LADON_COMPLETION_REQUEST "):
            payload = json.loads(text.split(" ", 1)[1])
            sequence.append(("application", payload))
            if application_limit is not None:
                flags = {application_limit: True}
                return ProcessResult(
                    tuple(command), 1, "", "bounded", 0.25,
                    peak_rss_bytes=1024, **flags,
                )
            output = _completion_frame(
                payload, context, status=application_status, goal_id=goal_id,
            )
            if duplicate_application:
                output += "\n" + output
        elif any(kind == "application" for kind, _payload in sequence):
            generated = Path(command[-1])
            assert generated.suffix == ".lean"
            assert "--run" not in command
            assert payload_bytes == b""
            source_text = generated.read_text(encoding="utf-8")
            assert "True.intro" in source_text
            prefix = "-- LADON_COMPLETION_REPLAY_REQUEST "
            request_line = next(line for line in source_text.splitlines() if line.startswith(prefix))
            payload = json.loads(request_line[len(prefix):])
            declaration_body = source_text.split("\n" + prefix, 1)[0]
            assert _digest(declaration_body.encode()) == payload["sourceDigest"]
            assert f"def {payload['declaration']}" in declaration_body
            output = "" if missing_replay else _replay_frame(
                payload, axioms=axioms, coverage=coverage,
            )
            sequence.append(("replay", {**payload, "_generatedPath": str(generated)}))
        else:
            pytest.fail(f"unexpected scripted runner input prefix: {text[:80]!r}")
        return ProcessResult(tuple(command), 0, output, "", 0.01, peak_rss_bytes=1024)

    return complete_source_goal(request, runner=runner), sequence, source_path, request


def _assert_replay_bindings(replay: dict[str, Any], application: dict[str, Any]) -> None:
    for key in ("requestId", "captureId", "termDigest"):
        assert replay[key] == application[key]
    assert replay["declaration"]


def _assert_completed_result(result: dict[str, Any]) -> None:
    assert result["status"] == "completed", result
    application_result = result["application"]
    original = application_result.get("originalGoal", {})
    assert application_result.get("goalId", original.get("goalId")) == "_uniq.1"
    assert result["replay"]["coverage"] == "complete"
    assert result["trust"]["coverage"] == "complete"
    assert result["trust"]["accepted"] is True


def _assert_workflow_cleanup(sequence: list[tuple[str, dict[str, Any]]]) -> None:
    assert all(not Path(payload["snapshotPath"]).exists() for _, payload in sequence[:2])
    assert not Path(sequence[-1][1]["_generatedPath"]).exists()


def test_completed_requires_fresh_capture_application_and_independent_replay(tmp_path, monkeypatch):
    result, sequence, _source, _request = _workflow(tmp_path, monkeypatch)

    assert [kind for kind, _ in sequence] == ["capture", "capture", "application", "replay"]
    _assert_replay_bindings(sequence[3][1], sequence[2][1])
    _assert_completed_result(result)
    _assert_workflow_cleanup(sequence)


def test_public_capture_fixture_is_a_valid_two_observation_input(tmp_path, monkeypatch):
    _repo, _source, _context, request, capture_source_goal = _fixture(tmp_path, monkeypatch)
    captured = _valid_capture(_context, _source, capture_source_goal, request)

    assert captured["scope"] == "source-goal-elaboration-observation"
    assert captured["replay"] == "not-run"
    assert captured["goal"]["typeStructural"] == "Lean.Expr.const `True []"
    assert captured["captureId"].startswith("sha256:")


def test_wrong_selected_goal_and_duplicate_terminal_frames_fail_closed(tmp_path, monkeypatch):
    wrong_root = tmp_path / "wrong"
    wrong_root.mkdir()
    wrong, wrong_sequence, _source, _request = _workflow(
        wrong_root, monkeypatch, goal_id="_uniq.other",
    )
    assert [kind for kind, _ in wrong_sequence][-1] == "application"
    assert wrong["status"] in {"rejected", "stale", "unavailable"}
    assert wrong["status"] != "completed"

    duplicate_root = tmp_path / "duplicate"
    duplicate_root.mkdir()
    duplicate, duplicate_sequence, _source, _request = _workflow(
        duplicate_root, monkeypatch, duplicate_application=True,
    )
    assert [kind for kind, _ in duplicate_sequence][-1] == "application"
    assert duplicate["status"] in {"unavailable", "rejected"}
    assert duplicate["status"] != "completed"


def test_missing_independent_replay_frame_never_completes(tmp_path, monkeypatch):
    result, sequence, _source, _request = _workflow(
        tmp_path, monkeypatch, missing_replay=True,
    )
    assert [kind for kind, _ in sequence][-1] == "replay"
    assert result["status"] == "unavailable", result
    assert result["trust"]["coverage"] == "unavailable"
    assert not Path(sequence[-1][1]["_generatedPath"]).exists()


@pytest.mark.parametrize(("flag", "expected"), [
    ("timed_out", "timeout"), ("memory_limited", "memory-limit"),
    ("output_limited", "output-limit"),
])
def test_process_bounds_stop_before_replay_and_clean_snapshot(tmp_path, monkeypatch, flag, expected):
    result, sequence, _source, _request = _workflow(
        tmp_path, monkeypatch, application_limit=flag,
    )
    assert [kind for kind, _ in sequence] == ["capture", "capture", "application"]
    assert result["status"] == expected, result
    assert not Path(sequence[-1][1]["snapshotPath"]).exists()


@pytest.mark.parametrize(("application_status", "expected"), [("incomplete", "incomplete"), ("rejected", "rejected")])
def test_residual_or_type_rejection_never_claims_completion(tmp_path, monkeypatch, application_status, expected):
    result, sequence, _source, _request = _workflow(
        tmp_path, monkeypatch, application_status=application_status,
    )
    assert [kind for kind, _ in sequence] == ["capture", "capture", "application"]
    assert result["status"] == expected, result
    assert result["replay"]["status"] == "not-run"
    if application_status == "incomplete":
        assert result["application"]["residualGoals"]


@pytest.mark.parametrize(("axioms", "coverage", "expected"), [
    (["Classical.choice"], "complete", "completed"),
    (["sorryAx"], "complete", "trust-rejected"),
    (["Unapproved.secret"], "complete", "trust-rejected"),
    (None, "unavailable", "unavailable"),
])
def test_placeholder_unknown_axiom_and_missing_coverage_block_completion(tmp_path, monkeypatch, axioms, coverage, expected):
    result, sequence, _source, _request = _workflow(
        tmp_path, monkeypatch, axioms=axioms, coverage=coverage,
    )
    assert [kind for kind, _ in sequence][-1] == "replay"
    assert result["status"] == expected, result
    assert result["trust"]["accepted"] is (expected == "completed")
    if coverage == "unavailable":
        assert result["trust"]["observedAxioms"] is None


def test_source_change_during_fresh_capture_is_stale_and_does_not_continue(tmp_path, monkeypatch):
    repo, source_path, context, capture_request, capture_source_goal = _fixture(tmp_path, monkeypatch)
    capture = _valid_capture(context, source_path, capture_source_goal, capture_request)
    from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

    request = SourceGoalCompletionRequest(repo_root=repo, capture=capture, term="True.intro", toolchain=context)
    seen = 0
    snapshots: list[Path] = []

    def runner(command, **options):
        nonlocal seen
        payload = json.loads(options["input_bytes"].decode().split(" ", 1)[1])
        snapshots.append(Path(payload["snapshotPath"]))
        seen += 1
        output = _source_observation(payload, context)
        if seen == 2:
            source_path.write_text(SOURCE + "-- changed\n", encoding="utf-8")
        return ProcessResult(tuple(command), 0, output, "", 0.01, peak_rss_bytes=1024)

    result = complete_source_goal(request, runner=runner)
    assert result["status"] == "stale", result
    assert seen == 2
    assert all(not path.exists() for path in snapshots)
