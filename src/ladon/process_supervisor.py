"""Bounded supervision for subprocesses started in target Lean repositories.

Target commands may execute untrusted project code.  They therefore run in a
separate process group with captured output, a finite deadline, and explicit
group cleanup on timeout or caller interruption.
"""

from __future__ import annotations

import os
import queue
import signal
import subprocess
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Callable, IO, Iterator, Sequence


TERMINATE_GRACE_SECONDS = 2.0


class ProcessSignal(BaseException):
    """A caller termination signal received while a target group was active."""

    def __init__(self, signum: int) -> None:
        super().__init__(signum)
        self.signum = signum


class ProcessCancelled(RuntimeError):
    """A caller cancellation token became set during target execution."""


@dataclass(frozen=True)
class ProcessResult:
    """Completed target-process state, including bounded-failure details."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    elapsed_seconds: float
    timed_out: bool = False

    @property
    def succeeded(self) -> bool:
        """Whether the command completed normally with status zero."""

        return not self.timed_out and self.returncode == 0


def run_target_process(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: float,
    cancel_event: threading.Event | None = None,
    terminate_grace_seconds: float = TERMINATE_GRACE_SECONDS,
) -> ProcessResult:
    """Run one cancellable command with whole-process-group cleanup."""

    if timeout_seconds <= 0:
        raise ValueError("target-process timeout must be greater than zero")
    normalized = tuple(str(part) for part in command)
    raise_if_cancelled(cancel_event)
    started = monotonic()
    process = subprocess.Popen(
        normalized,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        with termination_signal_handler():
            stdout, stderr = communicate_until_terminal(
                process,
                timeout_seconds=timeout_seconds,
                started=started,
                cancel_event=cancel_event,
            )
    except subprocess.TimeoutExpired:
        stdout, stderr = terminate_process_group(
            process,
            terminate_grace_seconds=terminate_grace_seconds,
        )
        return ProcessResult(
            normalized,
            process.returncode if process.returncode is not None else -signal.SIGKILL,
            stdout,
            stderr,
            monotonic() - started,
            timed_out=True,
        )
    except BaseException:
        terminate_process_group(
            process,
            terminate_grace_seconds=terminate_grace_seconds,
        )
        raise
    return ProcessResult(
        normalized,
        process.returncode,
        stdout,
        stderr,
        monotonic() - started,
    )


def communicate_until_terminal(
    process: subprocess.Popen[str],
    *,
    timeout_seconds: float,
    started: float,
    cancel_event: threading.Event | None,
) -> tuple[str, str]:
    """Drain output while polling both the finite deadline and cancellation."""

    while True:
        raise_if_cancelled(cancel_event)
        remaining = timeout_seconds - (monotonic() - started)
        if remaining <= 0:
            raise subprocess.TimeoutExpired(process.args, timeout_seconds)
        try:
            return process.communicate(timeout=min(0.05, remaining))
        except subprocess.TimeoutExpired:
            continue


def run_streaming_target_process(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: float,
    input_text: str,
    stdout_line_validator: Callable[[str], None],
    cancel_event: threading.Event | None = None,
    terminate_grace_seconds: float = TERMINATE_GRACE_SECONDS,
) -> ProcessResult:
    """Run a framed command with live validation and cancellable cleanup."""

    if timeout_seconds <= 0:
        raise ValueError("target-process timeout must be greater than zero")
    normalized = tuple(str(part) for part in command)
    raise_if_cancelled(cancel_event)
    started = monotonic()
    process = streaming_process(normalized, cwd)
    streams = start_stream_drains(process)
    write_process_input(process, input_text)
    try:
        with termination_signal_handler():
            supervise_stream(
                process,
                streams.stdout_lines,
                timeout_seconds,
                started,
                stdout_line_validator,
                cancel_event,
            )
    except BaseException:
        terminate_streaming_group(process, streams, terminate_grace_seconds)
        raise
    process.wait()
    streams.join()
    return ProcessResult(
        normalized,
        process.returncode,
        "".join(streams.stdout),
        "".join(streams.stderr),
        monotonic() - started,
    )


@dataclass
class StreamDrains:
    """Concurrent pipe drains and their captured output."""

    stdout: list[str]
    stderr: list[str]
    stdout_lines: queue.Queue[str | None]
    threads: tuple[threading.Thread, threading.Thread]

    def join(self) -> None:
        """Wait for both finite drain threads."""

        for thread in self.threads:
            thread.join()


def streaming_process(
    command: tuple[str, ...],
    cwd: Path,
) -> subprocess.Popen[str]:
    """Start one session-isolated process with all standard pipes."""

    return subprocess.Popen(
        command,
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        bufsize=1,
    )


def start_stream_drains(process: subprocess.Popen[str]) -> StreamDrains:
    """Start stdout/stderr drains before writing request input."""

    if process.stdout is None or process.stderr is None:
        raise RuntimeError("target process pipes were not created")
    stdout: list[str] = []
    stderr: list[str] = []
    stdout_lines: queue.Queue[str | None] = queue.Queue()
    stdout_thread = threading.Thread(
        target=drain_stream,
        args=(process.stdout, stdout, stdout_lines),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=drain_stream,
        args=(process.stderr, stderr, None),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    return StreamDrains(
        stdout,
        stderr,
        stdout_lines,
        (stdout_thread, stderr_thread),
    )


def drain_stream(
    stream: IO[str],
    sink: list[str],
    lines: queue.Queue[str | None] | None,
) -> None:
    """Drain one pipe to EOF, optionally publishing complete stdout lines."""

    try:
        for line in stream:
            sink.append(line)
            if lines is not None:
                lines.put(line)
    finally:
        stream.close()
        if lines is not None:
            lines.put(None)


def write_process_input(process: subprocess.Popen[str], input_text: str) -> None:
    """Send one finite request and tolerate an early helper exit."""

    if process.stdin is None:
        raise RuntimeError("target process stdin pipe was not created")
    try:
        process.stdin.write(input_text)
        process.stdin.flush()
    except BrokenPipeError:
        pass
    finally:
        process.stdin.close()


def supervise_stream(
    process: subprocess.Popen[str],
    lines: queue.Queue[str | None],
    timeout_seconds: float,
    started: float,
    validator: Callable[[str], None],
    cancel_event: threading.Event | None,
) -> None:
    """Validate stdout until EOF while enforcing deadline and cancellation."""

    stdout_finished = False
    while not stdout_finished or process.poll() is None:
        raise_if_cancelled(cancel_event)
        remaining = timeout_seconds - (monotonic() - started)
        if remaining <= 0:
            raise subprocess.TimeoutExpired(process.args, timeout_seconds)
        try:
            line = lines.get(timeout=min(0.05, remaining))
        except queue.Empty:
            continue
        if line is None:
            stdout_finished = True
        else:
            validator(line)


def raise_if_cancelled(cancel_event: threading.Event | None) -> None:
    """Raise a classified cancellation when the caller token is set."""

    if cancel_event is not None and cancel_event.is_set():
        raise ProcessCancelled("target process cancelled by caller")


def terminate_streaming_group(
    process: subprocess.Popen[str],
    streams: StreamDrains,
    terminate_grace_seconds: float,
) -> None:
    """Terminate a streaming process group, drain remaining bytes, and reap."""

    signal_process_group(process, signal.SIGTERM)
    try:
        process.wait(timeout=max(0.0, terminate_grace_seconds))
    except subprocess.TimeoutExpired:
        signal_process_group(process, signal.SIGKILL)
        process.wait()
    streams.join()


def terminate_process_group(
    process: subprocess.Popen[str],
    *,
    terminate_grace_seconds: float,
) -> tuple[str, str]:
    """Terminate, escalate, drain, and reap a subprocess and its descendants."""

    signal_process_group(process, signal.SIGTERM)
    try:
        return process.communicate(timeout=max(0.0, terminate_grace_seconds))
    except subprocess.TimeoutExpired:
        signal_process_group(process, signal.SIGKILL)
        return process.communicate()


def signal_process_group(process: subprocess.Popen[str], signum: signal.Signals) -> None:
    """Signal the target group, tolerating a process that already exited."""

    try:
        os.killpg(process.pid, signum)
    except ProcessLookupError:
        return


@contextmanager
def termination_signal_handler() -> Iterator[None]:
    """Turn SIGTERM into a cleanup-capable exception on the main thread."""

    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = signal.getsignal(signal.SIGTERM)

    def raise_process_signal(signum: int, _frame: object) -> None:
        raise ProcessSignal(signum)

    signal.signal(signal.SIGTERM, raise_process_signal)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)
