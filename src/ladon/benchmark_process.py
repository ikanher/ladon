"""Bounded subprocess and Linux resource sampling for benchmark runs."""

from __future__ import annotations

import os
import platform
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


SAMPLE_INTERVAL_SECONDS = 0.01


@dataclass(frozen=True)
class MeasuredProcess:
    """One bounded process result with platform-qualified resource evidence."""

    returncode: int
    stdout: str
    stderr: str
    wall_seconds: float
    peak_rss_mib: float | None
    descendant_count: int | None
    timed_out: bool = False

    def to_json(self) -> dict[str, object]:
        """Return stable machine-readable process measurements."""

        return {
            "returncode": self.returncode,
            "wallSeconds": round(self.wall_seconds, 6),
            "peakRssMiB": self.peak_rss_mib,
            "descendantCount": self.descendant_count,
            "timedOut": self.timed_out,
        }


def run_measured(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    timeout_seconds: float,
) -> MeasuredProcess:
    """Run one process with a finite deadline and best-effort resource samples."""

    started = time.monotonic()
    process = subprocess.Popen(
        list(command),
        cwd=cwd,
        env=dict(environment),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    sampler = ProcessSampler(process.pid)
    timed_out = poll_until_exit(process, sampler, started, timeout_seconds)
    if timed_out:
        terminate_process_group(process)
    stdout, stderr = process.communicate()
    sampler.sample()
    return MeasuredProcess(
        returncode=process.returncode,
        stdout=stdout,
        stderr=stderr,
        wall_seconds=time.monotonic() - started,
        peak_rss_mib=sampler.peak_rss_mib,
        descendant_count=sampler.descendant_count,
        timed_out=timed_out,
    )


def poll_until_exit(
    process: subprocess.Popen[str],
    sampler: ProcessSampler,
    started: float,
    timeout_seconds: float,
) -> bool:
    """Poll and sample until exit, returning whether the deadline elapsed."""

    while process.poll() is None:
        sampler.sample()
        if time.monotonic() - started >= timeout_seconds:
            return True
        time.sleep(SAMPLE_INTERVAL_SECONDS)
    return False


def terminate_process_group(process: subprocess.Popen[str]) -> None:
    """Terminate then kill one isolated benchmark process group."""

    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=1)
    except ProcessLookupError:
        return
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=1)


class ProcessSampler:
    """Best-effort Linux `/proc` sampler with explicit unsupported state."""

    def __init__(self, root_pid: int) -> None:
        self.root_pid = root_pid
        self.supported = Path("/proc").is_dir() and platform.system() == "Linux"
        self.peak_rss_kib = 0
        self.seen_descendants: set[int] = set()

    def sample(self) -> None:
        """Record aggregate RSS and descendant identities for one instant."""

        if not self.supported:
            return
        descendants = descendant_pids(self.root_pid)
        self.seen_descendants.update(descendants)
        rss = sum(process_rss_kib(pid) for pid in {self.root_pid, *descendants})
        self.peak_rss_kib = max(self.peak_rss_kib, rss)

    @property
    def peak_rss_mib(self) -> float | None:
        """Return sampled aggregate RSS, or null on unsupported platforms."""

        if not self.supported:
            return None
        return round(self.peak_rss_kib / 1024, 3)

    @property
    def descendant_count(self) -> int | None:
        """Return unique observed descendants, or null when unsupported."""

        return len(self.seen_descendants) if self.supported else None


def descendant_pids(root_pid: int) -> set[int]:
    """Return currently live recursive descendants from `/proc` parent ids."""

    parent_by_pid = proc_parent_map()
    descendants: set[int] = set()
    frontier = {root_pid}
    while frontier:
        children = {
            pid
            for pid, parent in parent_by_pid.items()
            if parent in frontier and pid not in descendants
        }
        descendants.update(children)
        frontier = children
    return descendants


def proc_parent_map() -> dict[int, int]:
    """Return parseable Linux process parent ids."""

    rows: dict[int, int] = {}
    for stat_path in Path("/proc").glob("[0-9]*/stat"):
        parsed = parse_proc_stat(stat_path)
        if parsed is not None:
            rows[parsed[0]] = parsed[1]
    return rows


def parse_proc_stat(path: Path) -> tuple[int, int] | None:
    """Parse PID and PPID while tolerating spaces in process names."""

    try:
        text = path.read_text(encoding="utf-8")
        pid_text, remainder = text.split(" ", 1)
        fields = remainder.rsplit(")", 1)[1].split()
        return int(pid_text), int(fields[1])
    except (IndexError, OSError, ValueError):
        return None


def process_rss_kib(pid: int) -> int:
    """Return one Linux process resident-set sample in KiB."""

    try:
        rows = (Path("/proc") / str(pid) / "status").read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError:
        return 0
    value = next((row for row in rows if row.startswith("VmRSS:")), "")
    fields = value.split()
    return int(fields[1]) if len(fields) >= 2 else 0


def platform_capabilities() -> dict[str, object]:
    """Return explicit resource-sampling support and platform identity."""

    linux_proc = Path("/proc").is_dir() and platform.system() == "Linux"
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "peakRss": {
            "supported": linux_proc,
            "method": "linux_proc_tree_sampling" if linux_proc else "unsupported",
        },
        "descendantCount": {
            "supported": linux_proc,
            "method": "linux_proc_ppid_sampling" if linux_proc else "unsupported",
        },
    }
