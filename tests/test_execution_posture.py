from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ladon.execution_posture import TargetIsolationUnavailable
from ladon.proof_search_cli import proof_search_main
from ladon.semantic_candidate_worker import SemanticCandidateRequest
from ladon.verified_discovery import DiscoveryRequest


@pytest.mark.parametrize("request_type", [SemanticCandidateRequest, DiscoveryRequest])
def test_api_rejects_required_isolation_before_execution(request_type: type) -> None:
    arguments = (Path("/does-not-exist"), "Main", "True")
    if request_type is SemanticCandidateRequest:
        arguments += ("Main.proof",)
    with pytest.raises(TargetIsolationUnavailable, match="required but unavailable"):
        request_type(*arguments, require_isolation=True)
    with pytest.raises(TypeError, match="boolean"):
        request_type(*arguments, require_isolation="false")


@pytest.mark.parametrize("operation", [["check", "candidate"], ["discover"]])
def test_cli_isolation_rejection_precedes_preflight_and_publication(
    tmp_path: Path, operation: list[str], monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("rejected policy attempted preflight or target execution")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    output = tmp_path / "result.json"
    evidence_store = tmp_path / "evidence.sqlite"
    status = proof_search_main([
        *operation, "--repo-root", str(tmp_path), "--module", "Main", "--goal", "True",
        "--candidate", "Main.proof", "--require-isolation", "--output", str(output),
        "--evidence-store", str(evidence_store), "--index", str(tmp_path / "index.sqlite"),
    ])

    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    diagnostic = json.loads(captured.err)
    assert diagnostic["exitClass"] == "operational"
    assert diagnostic["diagnostic"]["code"] == "target-isolation-unavailable"
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("operation", [["check", "candidate"], ["discover"]])
@pytest.mark.parametrize("projection", ["llm", "review", "audit"])
@pytest.mark.parametrize("output_format", ["json", "text"])
def test_installed_console_fails_closed_before_explicit_tools(
    tmp_path: Path, operation: list[str], projection: str, output_format: str,
) -> None:
    console = os.environ.get("LADON_CONSOLE", str(Path(sys.executable).with_name("ladon")))
    marker = tmp_path / "preflight-ran"
    tool = tmp_path / "target-tool"
    tool.write_text(
        f"#!{sys.executable}\nfrom pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed')\n",
        encoding="utf-8",
    )
    tool.chmod(0o755)
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    before = set(tmp_path.iterdir())
    completed = subprocess.run([
        console, "proof-search", *operation, "--repo-root", str(tmp_path),
        "--module", "Main", "--goal", "True", "--candidate", "Main.proof",
        "--toolchain-mode", "explicit", "--lake-path", str(tool), "--lean-path", str(tool),
        "--require-isolation", "--projection", projection, "--format", output_format,
        "--output", str(tmp_path / "result.json"),
        "--evidence-store", str(tmp_path / "evidence.sqlite"),
    ], cwd=tmp_path, text=True, capture_output=True, timeout=10, check=False)

    assert completed.returncode == 1
    assert completed.stdout == ""
    diagnostic = json.loads(completed.stderr)
    assert diagnostic["diagnostic"]["code"] == "target-isolation-unavailable"
    assert set(tmp_path.iterdir()) == before
