from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from ladon.process_supervisor import (
    ProcessCancelled,
    run_bounded_target_process,
    run_streaming_target_process,
    run_target_process,
)


def test_target_process_captures_output_and_status(tmp_path: Path) -> None:
    result = run_target_process(
        [
            sys.executable,
            "-c",
            "import sys; print('out'); print('err', file=sys.stderr)",
        ],
        cwd=tmp_path,
        timeout_seconds=2,
    )

    assert result.succeeded is True
    assert result.stdout == "out\n"
    assert result.stderr == "err\n"


def test_target_process_timeout_kills_descendant_group(tmp_path: Path) -> None:
    child_pid_path = tmp_path / "child.pid"
    program = (
        "import pathlib, subprocess, sys, time; "
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
        f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid)); "
        "time.sleep(60)"
    )

    result = run_target_process(
        [sys.executable, "-c", program],
        cwd=tmp_path,
        timeout_seconds=0.3,
        terminate_grace_seconds=0.3,
    )

    assert result.timed_out is True
    assert result.succeeded is False
    child_pid = int(child_pid_path.read_text(encoding="utf-8"))
    assert process_is_live(child_pid) is False


def test_target_process_escalates_when_group_ignores_termination(
    tmp_path: Path,
) -> None:
    program = (
        "import signal, time; "
        "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
        "time.sleep(60)"
    )

    result = run_target_process(
        [sys.executable, "-c", program],
        cwd=tmp_path,
        timeout_seconds=0.2,
        terminate_grace_seconds=0.1,
    )

    assert result.timed_out is True
    assert result.returncode == -signal.SIGKILL


def test_target_process_drains_large_stdout_and_stderr(tmp_path: Path) -> None:
    size = 256 * 1024
    program = (
        "import sys; "
        f"sys.stdout.write('o' * {size}); "
        f"sys.stderr.write('e' * {size})"
    )

    result = run_target_process(
        [sys.executable, "-c", program],
        cwd=tmp_path,
        timeout_seconds=3,
    )

    assert len(result.stdout) == size
    assert len(result.stderr) == size


def test_bounded_target_process_stops_oversized_output(tmp_path: Path) -> None:
    result = run_bounded_target_process(
        [
            sys.executable,
            "-c",
            ("import sys, time; "
            "sys.stdout.write('x' * 2000000); sys.stdout.flush(); time.sleep(60)"),
        ],
        cwd=tmp_path,
        timeout_seconds=3,
        max_output_bytes=4096,
        terminate_grace_seconds=0.1,
    )

    assert result.output_limited is True
    assert result.succeeded is False
    assert len(result.stdout.encode()) <= 4096


def test_bounded_target_process_classifies_fast_oversized_output(
    tmp_path: Path,
) -> None:
    result = run_bounded_target_process(
        [
            sys.executable,
            "-c",
            ("import sys; sys.stdout.write('o' * 5000); "
            "sys.stderr.write('e' * 5000)"),
        ],
        cwd=tmp_path,
        timeout_seconds=3,
        max_output_bytes=4096,
    )

    assert result.output_limited is True
    assert len(result.stdout.encode()) + len(result.stderr.encode()) <= 4096


def test_bounded_target_process_uses_explicit_environment(tmp_path: Path) -> None:
    result = run_bounded_target_process(
        [
            sys.executable,
            "-c",
            "import os; print(os.environ.get('CAPSULE_TEST', 'missing'))",
        ],
        cwd=tmp_path,
        timeout_seconds=3,
        max_output_bytes=4096,
        env={"CAPSULE_TEST": "present"},
    )

    assert result.succeeded is True
    assert result.stdout == "present\n"


@pytest.mark.skipif(not Path("/proc").is_dir(), reason="RSS enforcement needs /proc")
def test_bounded_target_process_stops_process_tree_over_rss_limit(
    tmp_path: Path,
) -> None:
    result = run_bounded_target_process(
        [
            sys.executable,
            "-c",
            "import time; payload = bytearray(64 * 1024 * 1024); time.sleep(60)",
        ],
        cwd=tmp_path,
        timeout_seconds=3,
        max_output_bytes=4096,
        max_rss_bytes=16 * 1024 * 1024,
        terminate_grace_seconds=0.1,
    )

    assert result.memory_limited is True
    assert result.succeeded is False
    assert result.peak_rss_bytes is not None
    assert result.peak_rss_bytes > 16 * 1024 * 1024


def test_streaming_process_cancellation_reaps_group(tmp_path: Path) -> None:
    cancel = threading.Event()
    timer = threading.Timer(0.15, cancel.set)
    timer.start()
    try:
        with pytest.raises(ProcessCancelled):
            run_streaming_target_process(
                [sys.executable, "-c", "import time; time.sleep(60)"],
                cwd=tmp_path,
                timeout_seconds=3,
                input_text="{}\n",
                stdout_line_validator=lambda _line: None,
                cancel_event=cancel,
                terminate_grace_seconds=0.1,
            )
    finally:
        timer.cancel()


def test_non_streaming_cancellation_reaps_descendant_group(
    tmp_path: Path,
) -> None:
    child_pid_path = tmp_path / "cancelled-child.pid"
    program = (
        "import pathlib, subprocess, sys, time; "
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
        f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid)); "
        "time.sleep(60)"
    )
    cancel = threading.Event()
    timer = threading.Timer(0.15, cancel.set)
    timer.start()
    try:
        with pytest.raises(ProcessCancelled):
            run_target_process(
                [sys.executable, "-c", program],
                cwd=tmp_path,
                timeout_seconds=3,
                cancel_event=cancel,
                terminate_grace_seconds=0.1,
            )
    finally:
        timer.cancel()

    child_pid = int(child_pid_path.read_text(encoding="utf-8"))
    assert process_is_live(child_pid) is False


def test_pre_cancelled_target_does_not_launch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cancel = threading.Event()
    cancel.set()

    def unexpected_launch(*_args, **_kwargs):
        raise AssertionError("pre-cancelled command launched")

    monkeypatch.setattr(subprocess, "Popen", unexpected_launch)

    with pytest.raises(ProcessCancelled):
        run_target_process(
            [sys.executable, "-c", "pass"],
            cwd=tmp_path,
            timeout_seconds=3,
            cancel_event=cancel,
        )


def test_stream_validation_failure_kills_descendant_group(tmp_path: Path) -> None:
    child_pid_path = tmp_path / "stream-child.pid"
    program = (
        "import pathlib, subprocess, sys, time; "
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
        f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid)); "
        "print('bad-frame', flush=True); "
        "time.sleep(60)"
    )

    with pytest.raises(ValueError, match="bad frame"):
        run_streaming_target_process(
            [sys.executable, "-c", program],
            cwd=tmp_path,
            timeout_seconds=3,
            input_text="{}\n",
            stdout_line_validator=lambda _line: (_ for _ in ()).throw(
                ValueError("bad frame")
            ),
            terminate_grace_seconds=0.1,
        )

    child_pid = int(child_pid_path.read_text(encoding="utf-8"))
    assert process_is_live(child_pid) is False


def test_target_process_termination_preserves_status_and_cleans_descendant(
    tmp_path: Path,
) -> None:
    child_pid_path = tmp_path / "child.pid"
    driver = (
        "import pathlib, signal, sys; "
        "from ladon.process_supervisor import ProcessSignal, run_target_process; "
        "program = \"import pathlib, subprocess, sys, time; "
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
        f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid)); "
        "time.sleep(60)\"; "
        "status = 0; "
        "\ntry:\n"
        " run_target_process([sys.executable, '-c', program], "
        f"cwd=pathlib.Path({str(tmp_path)!r}), timeout_seconds=60)\n"
        "except ProcessSignal as exc:\n"
        " status = 128 + exc.signum\n"
        "sys.exit(status)"
    )
    supervisor = subprocess.Popen([sys.executable, "-c", driver], cwd=tmp_path)
    wait_for_path(child_pid_path)

    supervisor.send_signal(signal.SIGTERM)

    assert supervisor.wait(timeout=3) == 128 + signal.SIGTERM
    child_pid = int(child_pid_path.read_text(encoding="utf-8"))
    assert process_is_live(child_pid) is False


def process_is_live(pid: int) -> bool:
    """Treat a zombie as cleaned up even before the host init reaps it."""

    status_path = Path(f"/proc/{pid}/status")
    if not status_path.exists():
        return False
    try:
        rows = status_path.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, ProcessLookupError):
        return False
    state = next(line for line in rows if line.startswith("State:"))
    if "\tZ" in state:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def wait_for_path(path: Path) -> None:
    """Wait briefly for a subprocess fixture to publish its descendant PID."""

    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.01)
    raise AssertionError(f"timed out waiting for {path}")
