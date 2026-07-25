from __future__ import annotations

import os
import stat
import threading
from pathlib import Path

import pytest

from ladon.process_supervisor import ProcessCancelled
from ladon.target_build import (
    TargetPreflightError,
    run_lake_build,
    validate_compiled_state,
    validate_lake_preflight,
)


def test_fake_lake_build_records_command_toolchain_and_diagnostics(
    tmp_path: Path,
) -> None:
    lake = fake_lake(tmp_path, "printf 'built\\n'")
    (tmp_path / "lakefile.lean").write_text("package Tiny\n", encoding="utf-8")
    (tmp_path / "lean-toolchain").write_text(
        "leanprover/lean4:v4.20.0\n",
        encoding="utf-8",
    )

    phase = run_lake_build(
        tmp_path,
        lake_executable=str(lake),
        timeout_seconds=2,
    )

    assert phase.status == "complete"
    assert phase.command == (str(lake), "build")
    assert phase.toolchain == "leanprover/lean4:v4.20.0"
    assert phase.diagnostics == ("stdout: built",)
    assert phase.to_report_row()["required"] is True


def test_fake_lake_failure_is_a_failed_required_phase(tmp_path: Path) -> None:
    lake = fake_lake(tmp_path, "printf 'broken\\n' >&2; exit 7")
    (tmp_path / "lakefile.toml").write_text(
        'name = "Tiny"\n',
        encoding="utf-8",
    )

    phase = run_lake_build(
        tmp_path,
        lake_executable=str(lake),
        timeout_seconds=2,
    )

    assert phase.status == "failed"
    assert phase.diagnostics == ("stderr: broken",)


def test_lake_preflight_classifies_missing_manifest_and_toolchain(
    tmp_path: Path,
) -> None:
    with pytest.raises(TargetPreflightError, match="no lakefile"):
        validate_lake_preflight(tmp_path, lake_executable="/missing/lake")

    (tmp_path / "lakefile.lean").write_text("package Tiny\n", encoding="utf-8")
    with pytest.raises(TargetPreflightError, match="does not exist"):
        validate_lake_preflight(tmp_path, lake_executable="/missing/lake")


def test_no_build_lean_preflight_names_compiled_state_and_remedy(
    tmp_path: Path,
) -> None:
    with pytest.raises(TargetPreflightError, match=r"compiled project state.*--build"):
        validate_compiled_state(tmp_path, build_requested=False)

    compiled = tmp_path / ".lake" / "build" / "lib" / "lean"
    compiled.mkdir(parents=True)
    validate_compiled_state(tmp_path, build_requested=False)


def test_lake_build_cancellation_reaps_its_process_group(
    tmp_path: Path,
) -> None:
    child_pid_path = tmp_path / "build-child.pid"
    lake = fake_lake(
        tmp_path,
        f"sleep 60 & echo $! > {child_pid_path}; wait",
    )
    (tmp_path / "lakefile.lean").write_text("package Tiny\n", encoding="utf-8")
    cancel = threading.Event()
    timer = threading.Timer(0.2, cancel.set)
    timer.start()
    try:
        with pytest.raises(ProcessCancelled):
            run_lake_build(
                tmp_path,
                lake_executable=str(lake),
                timeout_seconds=3,
                cancel_event=cancel,
            )
    finally:
        timer.cancel()

    child_pid = int(child_pid_path.read_text(encoding="utf-8"))
    assert process_is_live(child_pid) is False


def fake_lake(repo_root: Path, body: str) -> Path:
    """Create one executable Lake stand-in in the target repository."""

    path = repo_root / "fake-lake"
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def process_is_live(pid: int) -> bool:
    """Return whether a non-zombie process remains after supervisor cleanup."""

    status_path = Path(f"/proc/{pid}/status")
    try:
        exists = status_path.exists()
    except ProcessLookupError:
        return False
    if not exists:
        return False
    try:
        state = next(
            line
            for line in status_path.read_text(encoding="utf-8").splitlines()
            if line.startswith("State:")
        )
    except (FileNotFoundError, ProcessLookupError):
        return False
    if "\tZ" in state:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True
