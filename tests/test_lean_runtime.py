from __future__ import annotations

import os
import stat
import threading
from pathlib import Path

import pytest

from ladon.ir import LeanModule
from ladon.lean_protocol import ModuleRequest
from ladon.lean_runtime import (
    LeanRuntimeConfig,
    RequestedModule,
    execute_lean_runtime,
    plan_batches,
    resolve_lean_version,
)
from ladon.process_supervisor import ProcessResult

FAKE_LAKE = r"""#!/usr/bin/env python3
import json
import os
import pathlib
import subprocess
import sys
import time

mode = os.environ.get("LADON_FAKE_HELPER_MODE", "success")
count_path = os.environ.get("LADON_FAKE_COUNT")
if count_path:
    with open(count_path, "a", encoding="utf-8") as stream:
        stream.write("batch\n")
request = json.loads(pathlib.Path(sys.argv[-1]).read_text(encoding="utf-8"))
completed = 0
failed = 0
for index, row in enumerate(request["modules"]):
    if mode == "malformed" and index == 1:
        print("not-json", flush=True)
        time.sleep(60)
    if mode == "version-mismatch" and index == 0:
        print(json.dumps({"frame": "module", "protocolVersion": "future"}), flush=True)
        time.sleep(60)
    payload = {
        "version": "fake-helper",
        "file": row["file"],
        "header": {"imports": []},
        "commands": [{
            "isDeclarationLike": True,
            "declarationName": "value",
            "declarationFullName": row["module"] + ".value",
            "referenceCandidates": [],
        }],
    }
    if mode == "mixed" and row["module"].endswith("B"):
        frame = {
            "frame": "module",
            "protocolVersion": request["protocolVersion"],
            **row,
            "status": "failed",
            "diagnostic": {
                "id": "lean.fixture_failure",
                "severity": "error",
                "message": "fixture rejected module",
            },
        }
        failed += 1
    else:
        frame = {
            "frame": "module",
            "protocolVersion": request["protocolVersion"],
            **row,
            "status": "ok",
            "payload": payload,
        }
        completed += 1
    print(json.dumps(frame), flush=True)
    if mode == "timeout" and index == 0:
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        pathlib.Path(os.environ["LADON_FAKE_CHILD_PID"]).write_text(str(child.pid))
        time.sleep(60)
print(json.dumps({
    "frame": "summary",
    "protocolVersion": request["protocolVersion"],
    "helperVersion": "fake-helper-v2",
    "leanVersion": "Lean 4.fake",
    "requested": len(request["modules"]),
    "completed": completed,
    "failed": failed,
}), flush=True)
"""


def test_lean_version_probe_forwards_run_cancellation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cancel = threading.Event()
    observed: list[threading.Event | None] = []

    def fake_run(*_args, **kwargs):
        observed.append(kwargs.get("cancel_event"))
        return ProcessResult(
            ("lake", "env", "lean", "--version"),
            0,
            "Lean 4.fixture\n",
            "",
            0.01,
        )

    monkeypatch.setattr("ladon.lean_runtime.run_target_process", fake_run)

    assert resolve_lean_version(tmp_path, cancel_event=cancel) == "Lean 4.fixture"
    assert observed == [cancel]


def test_batch_planning_meets_ceiling_bound_and_rejects_one() -> None:
    requests = tuple(ModuleRequest(index, f"Pkg.M{index}", f"Pkg/M{index}.lean") for index in range(5))

    batches = plan_batches(requests, 2)

    assert [len(batch) for batch in batches] == [2, 2, 1]
    with pytest.raises(ValueError, match="at least two"):
        plan_batches(requests, 1)


def test_inventory_runtime_uses_at_most_ceiling_helper_invocations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, helper, modules, requested = runtime_fixture(tmp_path, 5)
    count = tmp_path / "count.txt"
    install_fake_lake(tmp_path, monkeypatch)
    monkeypatch.setenv("LADON_FAKE_COUNT", str(count))

    result = execute_lean_runtime(
        repo_root=repo,
        helper_path=helper,
        requested=requested,
        modules=modules,
        cache_dir=None,
        config=LeanRuntimeConfig(batch_size=2),
    )

    assert result.counters["helper_invocations"] == 3
    assert count.read_text(encoding="utf-8").splitlines() == ["batch"] * 3
    assert list(result.payloads) == [f"Pkg.M{index}" for index in range(5)]


def test_mixed_failure_strict_mode_retains_success_and_diagnostics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, helper, modules, requested = named_runtime_fixture(tmp_path, ("Pkg.A", "Pkg.B"))
    install_fake_lake(tmp_path, monkeypatch)
    monkeypatch.setenv("LADON_FAKE_HELPER_MODE", "mixed")

    result = execute_lean_runtime(
        repo_root=repo,
        helper_path=helper,
        requested=requested,
        modules=modules,
        cache_dir=None,
        config=LeanRuntimeConfig(batch_size=2, strict=True),
    )

    assert list(result.payloads) == ["Pkg.A"]
    assert result.diagnostics[0]["subject"] == "Pkg.B"
    assert result.counters["strict_rejected"] == 1
    assert result.provenance["strictRejected"] is True


@pytest.mark.parametrize("mode", ["malformed", "version-mismatch"])
def test_live_protocol_failure_preserves_or_fills_deterministic_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    repo, helper, modules, requested = named_runtime_fixture(tmp_path, ("Pkg.A", "Pkg.B"))
    install_fake_lake(tmp_path, monkeypatch)
    monkeypatch.setenv("LADON_FAKE_HELPER_MODE", mode)

    result = execute_lean_runtime(
        repo_root=repo,
        helper_path=helper,
        requested=requested,
        modules=modules,
        cache_dir=None,
        config=LeanRuntimeConfig(batch_size=2, timeout_seconds=2),
    )

    assert result.counters["failed"] >= 1
    assert result.diagnostics
    if mode == "malformed":
        assert list(result.payloads) == ["Pkg.A"]
    else:
        assert result.payloads == {}


def test_timeout_preserves_prefix_and_kills_helper_descendant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, helper, modules, requested = named_runtime_fixture(tmp_path, ("Pkg.A", "Pkg.B"))
    child_pid = tmp_path / "child.pid"
    install_fake_lake(tmp_path, monkeypatch)
    monkeypatch.setenv("LADON_FAKE_HELPER_MODE", "timeout")
    monkeypatch.setenv("LADON_FAKE_CHILD_PID", str(child_pid))

    result = execute_lean_runtime(
        repo_root=repo,
        helper_path=helper,
        requested=requested,
        modules=modules,
        cache_dir=None,
        config=LeanRuntimeConfig(batch_size=2, timeout_seconds=0.3),
    )

    assert list(result.payloads) == ["Pkg.A"]
    assert result.counters["timed_out_batches"] == 1
    assert process_is_live(int(child_pid.read_text(encoding="utf-8"))) is False


def test_extraction_runtime_never_invokes_build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, helper, modules, requested = runtime_fixture(tmp_path, 2)
    count = tmp_path / "count.txt"
    install_fake_lake(tmp_path, monkeypatch)
    monkeypatch.setenv("LADON_FAKE_COUNT", str(count))

    result = execute_lean_runtime(
        repo_root=repo,
        helper_path=helper,
        requested=requested,
        modules=modules,
        cache_dir=None,
        config=LeanRuntimeConfig(),
        build_requested=False,
    )

    assert count.read_text(encoding="utf-8") == "batch\n"
    assert result.provenance["buildRequested"] is False
    assert result.provenance["buildInvokedByExtraction"] is False


def runtime_fixture(
    tmp_path: Path,
    count: int,
) -> tuple[Path, Path, dict[str, LeanModule], tuple[RequestedModule, ...]]:
    """Build a conventional multi-module runtime fixture."""

    names = tuple(f"Pkg.M{index}" for index in range(count))
    return named_runtime_fixture(tmp_path, names)


def named_runtime_fixture(
    tmp_path: Path,
    names: tuple[str, ...],
) -> tuple[Path, Path, dict[str, LeanModule], tuple[RequestedModule, ...]]:
    """Build source files and normalized request rows."""

    repo = tmp_path / "repo"
    repo.mkdir()
    modules: dict[str, LeanModule] = {}
    requested: list[RequestedModule] = []
    for name in names:
        relative = Path(*name.split(".")).with_suffix(".lean")
        source = repo / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"def {name}.value : Nat := 1\n", encoding="utf-8")
        modules[name] = LeanModule(name, str(relative))
        requested.append(RequestedModule(name, str(relative)))
    helper = tmp_path / "helper.lean"
    helper.write_text("-- fake helper path\n", encoding="utf-8")
    return repo, helper, modules, tuple(requested)


def install_fake_lake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Install the executable fake helper dispatcher at the front of PATH."""

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    lake = fake_bin / "lake"
    lake.write_text(FAKE_LAKE, encoding="utf-8")
    lake.chmod(lake.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")


def process_is_live(pid: int) -> bool:
    """Treat a zombie as cleaned while the host init finishes reaping it."""

    status = Path(f"/proc/{pid}/status")
    if not status.exists():
        return False
    state = next(
        line
        for line in status.read_text(encoding="utf-8").splitlines()
        if line.startswith("State:")
    )
    if "\tZ" in state:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True
