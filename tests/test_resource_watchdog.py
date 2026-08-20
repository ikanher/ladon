from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

import pytest

from ladon.cli import main, mark_resource_limit_failure, run_context_build
from ladon.pipeline import RunContext, run_pipeline
from ladon.process_supervisor import ProcessCancelled, run_target_process
from ladon.progress import (
    ResourceLimitExceeded,
    RunBudget,
    RunLimits,
    process_tree_rss_bytes,
)


def test_active_helper_limit_retains_partial_evidence_and_diagnostic(
    tmp_path: Path,
) -> None:
    source = tmp_path / "Tiny.lean"
    source.write_text("theorem tiny : True := True.intro\n", encoding="utf-8")
    child_pid_path = tmp_path / "helper-child.pid"

    def blocked_extractor(context, _discovery):
        program = (
            "import pathlib, subprocess, sys, time; "
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
            f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid)); "
            "time.sleep(60)"
        )
        run_target_process(
            [sys.executable, "-c", program],
            cwd=tmp_path,
            timeout_seconds=10,
            cancel_event=context.cancel_event,
            terminate_grace_seconds=0.1,
        )
        raise AssertionError("cancelled helper unexpectedly returned")

    context = RunContext(
        repo_root=tmp_path,
        requested_root="Tiny.lean",
        extraction_backend="lean",
        lean_extractor=blocked_extractor,
        source_cache_enabled=False,
        budget=RunBudget(
            RunLimits(wall_seconds=0.1),
            sample_interval_seconds=0.005,
        ),
    )

    result = run_pipeline(context)
    report = mark_resource_limit_failure(
        result.to_report_model(),
        context.limit_failure or {},
    )
    payload = report.to_dict()

    assert context.limit_failure is not None
    assert context.limit_failure["phase"] == "lean_extraction"
    phase = payload["phases"]["lean_extraction"]
    assert phase["status"] == "failed"
    assert phase["required"] is True
    assert phase["diagnostics"][-1]["id"] == "resource.overall_wall_time"
    assert result.module_dag["completeness"]["status"] == "partial"
    child_pid = int(child_pid_path.read_text(encoding="utf-8"))
    assert process_is_live(child_pid) is False


def test_explicit_build_uses_the_active_whole_run_watchdog(
    tmp_path: Path,
    monkeypatch,
) -> None:
    context = RunContext(
        repo_root=tmp_path,
        build_requested=True,
        budget=RunBudget(
            RunLimits(wall_seconds=0.02),
            sample_interval_seconds=0.005,
        ),
    )

    def blocked_build(*_args, cancel_event=None, **_kwargs):
        assert cancel_event is context.cancel_event
        while not cancel_event.wait(timeout=0.005):
            time.sleep(0)
        raise ProcessCancelled("cancelled build")

    monkeypatch.setattr("ladon.cli.run_lake_build", blocked_build)

    with pytest.raises(ResourceLimitExceeded) as crossing:
        run_context_build(context, timeout_seconds=10)

    assert crossing.value.phase == "build"
    assert context.limit_failure is not None
    assert context.limit_failure["id"] == "resource.overall_wall_time"


def test_supported_rss_limit_cancels_an_active_process_group(
    tmp_path: Path,
) -> None:
    baseline = process_tree_rss_bytes(os.getpid())
    if baseline is None:
        pytest.skip("process-tree RSS enforcement is unavailable")
    process_pid_path = tmp_path / "rss-process.pid"
    program = (
        "import os, pathlib, time; "
        f"pathlib.Path({str(process_pid_path)!r}).write_text(str(os.getpid())); "
        "payload = bytearray(32 * 1024 * 1024); "
        "payload[0] = 1; "
        "time.sleep(60)"
    )
    cancel = threading.Event()
    budget = RunBudget(
        RunLimits(rss_bytes=baseline + 8 * 1024 * 1024),
        sample_interval_seconds=0.01,
    )

    with pytest.raises(ResourceLimitExceeded) as crossing, budget.watch(
        "lean_extraction", cancel
    ):
            run_target_process(
                [sys.executable, "-c", program],
                cwd=tmp_path,
                timeout_seconds=5,
                cancel_event=cancel,
                terminate_grace_seconds=0.1,
            )

    assert crossing.value.kind == "process_tree_rss"
    assert crossing.value.observed > crossing.value.limit
    process_pid = int(process_pid_path.read_text(encoding="utf-8"))
    assert process_is_live(process_pid) is False


def test_trailing_build_limit_writes_retained_partial_report_and_reaps(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "Tiny.lean"
    source.write_text("theorem tiny : True := True.intro\n", encoding="utf-8")
    (tmp_path / "lakefile.lean").write_text("package Tiny\n", encoding="utf-8")
    child_pid_path = tmp_path / "cli-build-child.pid"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    lake = fake_bin / "lake"
    lake.write_text(
        "#!/bin/sh\n"
        f"sleep 60 & echo $! > {child_pid_path}\n"
        "wait\n",
        encoding="utf-8",
    )
    lake.chmod(lake.stat().st_mode | 0o100)
    monkeypatch.setenv("PATH", f"{fake_bin}:{os.environ.get('PATH', '')}")
    output = tmp_path / "partial.json"

    status = main(
        [
            "--repo-root",
            str(tmp_path),
            "--root",
            "Tiny.lean",
            "--build",
            "--overall-timeout",
            "0.3",
            "--no-cache",
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert status == 1
    assert payload["phases"]["build"]["status"] == "failed"
    resource = next(
        row
        for row in payload["diagnostics"]
        if row["id"] == "resource.overall_wall_time"
    )
    assert resource["ref"] in payload["phases"]["build"]["diagnosticRefs"]
    child_pid = int(child_pid_path.read_text(encoding="utf-8"))
    assert process_is_live(child_pid) is False


def process_is_live(pid: int) -> bool:
    """Return whether a non-zombie helper descendant survived cancellation."""

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
