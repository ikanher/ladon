"""Exercise discarded caller inputs through real child failures and renderers."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from support.execution_nonleakage import (
    assert_clean_files,
    assert_no_discarded_input,
    poison_environment,
)

from ladon.lean_toolchain import resolve_toolchain_context
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_search_cli import _write_payload, proof_search_main
from ladon.scratch_replay import replay_scratch
from ladon.semantic_candidate_batch_worker import check_semantic_candidates
from ladon.semantic_candidate_worker import (
    SEMANTIC_BATCH_PROTOCOL,
    UNIVERSE_POLICY,
    SemanticCandidateRequest,
    check_semantic_candidate,
)
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.semantic_result_projection import project_semantic_result


def _require_rss_capability(mode: str) -> None:
    if mode != "memory-limit" or Path("/proc").is_dir():
        return
    message = "RSS nonleakage qualification requires /proc process accounting"
    if os.environ.get("LADON_REQUIRE_EXECUTION_NONLEAKAGE") == "1":
        pytest.fail(message)
    pytest.skip(message)


@pytest.mark.parametrize("required", [False, True])
def test_unavailable_rss_is_optional_only_outside_required_qualification(
    monkeypatch: pytest.MonkeyPatch, required: bool,
) -> None:
    original_is_dir = Path.is_dir
    monkeypatch.setattr(
        Path, "is_dir", lambda path: False if path == Path("/proc") else original_is_dir(path),
    )
    monkeypatch.setenv("LADON_REQUIRE_EXECUTION_NONLEAKAGE", "1" if required else "0")
    _require_rss_capability("nonzero")
    expected = pytest.fail.Exception if required else pytest.skip.Exception
    with pytest.raises(expected, match="requires /proc process accounting"):
        _require_rss_capability("memory-limit")


def _repository(root: Path, mode: str, *, compiled: bool = True) -> tuple[Path, Path]:
    """Fake tools expose their actual process environment on the failing path."""
    (root / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n")
    library = root / ".lake" / "build" / "lib" / "lean"
    library.mkdir(parents=True)
    if compiled:
        (library / "Main.olean").write_bytes(b"compiled fixture")
    program = f'''#!{sys.executable}
import json, os, sys, time
from pathlib import Path
mode = {mode!r}
if "--version" in sys.argv:
    if mode == "version-failure":
        print(json.dumps(dict(os.environ)), file=sys.stderr)
        raise SystemExit(7)
    print("Lean version " + ("0.0.0" if mode == "pin-mismatch" else "4.20.0"))
    raise SystemExit(0)
observed_environment = json.dumps(dict(os.environ))
Path({str(root / '.lake' / 'worker-environment.json')!r}).write_text(observed_environment)
print(observed_environment, file=sys.stderr, flush=True)
if "--batch" in sys.argv and mode != "invalid-frame":
    offset = sys.argv.index("--batch")
    header = {{
        "protocol": {SEMANTIC_BATCH_PROTOCOL!r}, "frameVersion": 1,
        "frameKind": "header", "sequence": 0, "terminal": False,
        "universePolicy": {UNIVERSE_POLICY!r},
        "requestId": sys.argv[offset + 6],
        "goalRequestDigest": sys.argv[offset + 4],
        "executionContextRef": sys.argv[offset + 7],
        "leanVersion": "4.20.0", "leanCommit": "fixture",
        "executablePath": str(Path(__file__).resolve()),
        "module": sys.argv[offset + 1],
        "probe": {{"name": sys.argv[offset + 5], "typeDisplay": "True",
                   "typeStructural": "True"}},
        "importedModules": [{{"module": "Main", "oleanPath": {str(library / 'Main.olean')!r}}}],
        "localContext": [],
    }}
    print("LADON_FRAME " + json.dumps(header), flush=True)
if mode == "invalid-frame":
    print("LADON_FRAME {{", flush=True)
    raise SystemExit(0)
if mode == "output-limit":
    print("x" * 131072, flush=True)
if mode == "memory-limit":
    allocation = bytearray(64 * 1024 * 1024)
if mode in {{"timeout", "output-limit", "memory-limit"}}:
    time.sleep(60)
raise SystemExit(7)
'''
    for name in ("lake", "lean"):
        executable = root / name
        executable.write_text(program)
        executable.chmod(0o755)
    return root / "lake", root / "lean"


def _request(root: Path, tools: tuple[Path, Path]) -> SemanticCandidateRequest:
    context = resolve_toolchain_context(root, lake_path=tools[0], lean_path=tools[1])
    assert_no_discarded_input(context.to_dict())
    assert_no_discarded_input(dict(context.environment))
    return SemanticCandidateRequest(
        root, "Main", "True", "Main.fact", toolchain=context,
        timeout_seconds=1, max_output_bytes=4096, max_rss_bytes=32 * 1024 * 1024,
    )


def _observed_runner(observations: list):
    def run(command, **kwargs):
        assert_no_discarded_input(dict(kwargs["env"]))
        process = run_bounded_target_process(command, **kwargs)
        observations.append(process)
        assert_no_discarded_input(process.stdout)
        assert_no_discarded_input(process.stderr)
        observed = json.loads((kwargs["cwd"] / ".lake" / "worker-environment.json").read_text())
        assert "PATH" in observed
        assert_no_discarded_input(observed)
        return process

    return run


def _check_views(payload: dict, directory: Path) -> None:
    directory.mkdir()
    projections = ("audit", "llm", "review") if payload.get("operation") == "check-candidate" else ()
    views = {
        name: project_semantic_result(payload, projection=name, registered_artifacts={})
        for name in projections
    } or {"raw": payload}
    assert_no_discarded_input(payload)
    for name, view in views.items():
        assert_no_discarded_input(view)
        for output_format in ("json", "text"):
            _write_payload(
                view, output=str(directory / f"{name}.{output_format}"),
                output_format=output_format,
            )
    assert_clean_files(directory)


@pytest.mark.parametrize("mode", ["version-failure", "pin-mismatch"])
def test_poisoned_preflight_failure_diagnostics_do_not_publish_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], mode: str,
) -> None:
    tools = _repository(tmp_path, mode)
    poison_environment(monkeypatch)
    output, store = tmp_path / "result.json", tmp_path / "evidence.sqlite"
    status = proof_search_main([
        "check", "candidate", "--repo-root", str(tmp_path), "--module", "Main",
        "--goal", "True", "--candidate", "Main.fact", "--toolchain-mode", "explicit",
        "--lake-path", str(tools[0]), "--lean-path", str(tools[1]), "--progress",
        "--output", str(output), "--evidence-store", str(store), "--format", "json",
    ])
    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert_no_discarded_input(captured.err)
    diagnostic = json.loads(captured.err.splitlines()[-1])
    assert diagnostic["diagnostic"]["code"] == "toolchain-unavailable"
    assert not output.exists() and not store.exists()
    assert_clean_files(tmp_path)


def test_missing_compiled_module_drops_inputs_before_worker_or_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools = _repository(tmp_path, "nonzero", compiled=False)
    poison_environment(monkeypatch)
    request = _request(tmp_path, tools)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("missing compiled module launched a worker")

    result = check_semantic_candidate(request, runner=forbidden)
    assert result.status == "failed-checker"
    assert result.diagnostic["code"] == "compiled-module-unavailable"
    assert result.artifacts == ()
    _check_views(result.to_dict(), tmp_path / "views")
    assert_clean_files(tmp_path)


@pytest.mark.parametrize("mode,status", [
    ("nonzero", "failed-checker"), ("invalid-frame", "invalid-worker-output"),
    ("timeout", "timeout"), ("output-limit", "output-limited"), ("memory-limit", "memory-limited"),
])
def test_single_worker_failure_environment_receipts_and_views_are_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, status: str,
) -> None:
    _require_rss_capability(mode)
    tools = _repository(tmp_path, mode)
    poison_environment(monkeypatch)
    request = _request(tmp_path, tools)
    observations: list = []
    result = check_semantic_candidate(request, runner=_observed_runner(observations))
    assert len(observations) == 1
    assert result.status == status, result.diagnostic
    assert result.artifacts == ()
    _check_views(result.to_dict(), tmp_path / "views")
    assert_clean_files(tmp_path)


@pytest.mark.parametrize("mode,code", [
    ("nonzero", "batch-worker-failed"), ("invalid-frame", "invalid-batch-worker-output"),
    ("timeout", "batch-timeout"), ("output-limit", "batch-output-limit"),
    ("memory-limit", "batch-memory-limit"),
])
def test_batch_failure_preserves_clean_process_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, code: str,
) -> None:
    _require_rss_capability(mode)
    tools = _repository(tmp_path, mode)
    poison_environment(monkeypatch)
    request = _request(tmp_path, tools)
    observations: list = []
    result = check_semantic_candidates(
        request, ["Main.fact"], runner=_observed_runner(observations),
    )
    assert len(observations) == 1
    assert result.diagnostic["code"] == code
    assert result.rows == () and result.terminal is False
    _check_views(result.to_dict(), tmp_path / "views")
    assert_clean_files(tmp_path)


@pytest.mark.parametrize("mode,status", [
    ("nonzero", "process-failed"), ("timeout", "timeout"), ("output-limit", "output-limited"),
    ("memory-limit", "memory-limited"),
])
def test_scratch_failures_keep_child_environment_and_diagnostic_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, status: str,
) -> None:
    _require_rss_capability(mode)
    tools = _repository(tmp_path, mode)
    poison_environment(monkeypatch)
    request = _request(tmp_path, tools)
    observations: list = []
    result = replay_scratch(
        repo_root=tmp_path, module="Main", goal="True", candidate="Main.fact",
        toolchain=request.toolchain, timeout_seconds=1, max_output_bytes=4096,
        max_rss_bytes=request.max_rss_bytes,
        runner=_observed_runner(observations),
    )
    assert len(observations) == 1
    assert result.status == status
    _check_views(result.to_dict(), tmp_path / "views")
    assert_clean_files(tmp_path)


def test_ambient_preparation_filters_host_inputs_before_actual_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _repository(tmp_path, "nonzero")
    poison_environment(monkeypatch)
    monkeypatch.setenv("PATH", str(tmp_path))
    execution = prepare_direct_lean_execution(tmp_path, "Main", None)
    assert_no_discarded_input(dict(execution.environment))
    assert execution.environment["LEAN_PATH"] == str(tmp_path / ".lake/build/lib/lean")
    observations: list = []
    result = _observed_runner(observations)(
        execution.command, cwd=tmp_path, env=execution.environment,
        timeout_seconds=2, max_output_bytes=4096,
    )
    assert result.returncode == 7
    assert len(observations) == 1
    assert_clean_files(tmp_path)
