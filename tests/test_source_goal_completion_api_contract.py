"""Early-boundary API proposals; no helper/compiler protocol is assumed here."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


def _api():
    # The missing module is the intentional initial red for this new API.
    from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

    return SourceGoalCompletionRequest, complete_source_goal


def _toolchain(tmp_path: Path):
    from ladon.lean_toolchain import LeanToolchainContext, _identity, _source_tree_identity

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "lean-toolchain").write_text("leanprover/lean4:v4.32.1\n", encoding="utf-8")
    source = repo / "Owner.lean"
    source.write_text("example: True := by\n  skip\n", encoding="utf-8")
    binary_dir = tmp_path / "toolchain"
    binary_dir.mkdir()
    lean = binary_dir / "lean"
    lake = binary_dir / "lake"
    lean.write_bytes(b"fake lean identity for preflight-only tests")
    lake.write_bytes(b"fake lake identity for preflight-only tests")
    pin = (repo / "lean-toolchain").read_text(encoding="utf-8").strip()
    pin_digest = "sha256:" + hashlib.sha256(pin.encode()).hexdigest()
    context = LeanToolchainContext(
        repo_root=repo, lake_path=lake, lean_path=lean, pin_content=pin,
        pin_digest=pin_digest, lake_identity=_identity(lake), lean_identity=_identity(lean),
        source_tree_identity=_source_tree_identity(repo, None), lean_release="4.32.1",
        lean_commit="fixture-commit", selection_mode="explicit", environment_keys=(), environment={},
    )
    return repo, source, context


def _capture(context, source: Path) -> dict[str, object]:
    """Build a correctly hashed source-capture shape; API tests mutate one boundary at a time."""
    from ladon.source_goal_capture import SourceGoalCaptureRequest, _make_capture

    source_bytes = source.read_bytes()
    digest = "sha256:" + hashlib.sha256(source_bytes).hexdigest()
    req = SourceGoalCaptureRequest(
        repo_root=source.parent, source_path="Owner.lean", module="Owner", line=2,
        column=6, toolchain=context,
    )
    frame = {
        "byteOffset": 26, "rangeStartByte": 22, "rangeEndByte": 26, "selectionEndByte": 26,
        "goalCount": 1, "goals": [{
            "goalId": "_uniq.1", "typeDisplay": "True", "typeStructural": "Lean.Expr.const `True []",
            "localContext": [],
        }],
        "leanVersion": "4.32.1", "leanCommit": "fixture-commit",
        "leanExecutablePath": str(context.lean_path), "namespaceName": "Owner",
        "openDeclarationsStructural": "[]", "optionsStructural": "[]",
        "useAfter": False,
    }
    capture = _make_capture(
        req, source_bytes, frame, 0, {"modules": [], "environment": {}},
        "sha256:" + "1" * 64,
    )
    # The canonical capture must bind the exact source bytes used above.
    assert capture["source"]["digest"] == digest
    return capture


def test_capture_id_tampering_is_rejected_before_target_runner(tmp_path):
    repo, source, context = _toolchain(tmp_path)
    capture = _capture(context, source)
    capture["goal"]["typeStructural"] = "False"
    request_type, complete = _api()
    request = request_type(repo_root=repo, capture=capture, term="True.intro", toolchain=context)
    called = False

    def runner(*_args, **_kwargs):
        nonlocal called
        called = True
        pytest.fail("invalid capture identity must be rejected before target execution")

    result = complete(request, runner=runner)
    assert result["status"] in {"rejected", "stale"}
    assert result["diagnostic"]["code"] == "capture-identity-mismatch"
    assert called is False


@pytest.mark.parametrize("historical", [
    {"schema": "ladon-semantic-candidate-check-result-v1", "operation": "check-candidate", "status": "accepted"},
    {"schema": "ladon-semantic-scratch-result-v1", "operation": "scratch-compilation", "status": "compiled"},
])
def test_exploration_or_candidate_acceptance_is_not_a_source_capture(tmp_path, historical):
    repo, _source, context = _toolchain(tmp_path)
    request_type, complete = _api()
    request = request_type(repo_root=repo, capture=historical, term="True.intro", toolchain=context)

    def runner(*_args, **_kwargs):
        pytest.fail("historical acceptance must not be upgraded into completion")

    result = complete(request, runner=runner)
    assert result["status"] in {"rejected", "unavailable"}
    assert result.get("application") is None
    replay = result.get("replay")
    assert not isinstance(replay, dict) or replay.get("status") != "accepted"
