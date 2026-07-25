"""Diagnostic progress events and cooperative whole-run resource budgets."""

from __future__ import annotations

import json
import os
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic
from typing import Any, Iterator, TextIO


PROGRESS_SCHEMA_VERSION = 1
PROGRESS_MODES = frozenset({"auto", "plain", "json", "off"})
DEFAULT_PROGRESS_INTERVAL_SECONDS = 5.0
DEFAULT_RESOURCE_SAMPLE_INTERVAL_SECONDS = 0.25


class ResourceLimitExceeded(RuntimeError):
    """A configured whole-run resource limit crossed its supported boundary."""

    def __init__(
        self,
        *,
        kind: str,
        phase: str,
        observed: float | int,
        limit: float | int,
    ) -> None:
        self.kind = kind
        self.phase = phase
        self.observed = observed
        self.limit = limit
        super().__init__(
            f"{kind} limit exceeded during {phase}: observed {observed}, limit {limit}"
        )


@dataclass(frozen=True)
class RunLimits:
    """Finite caller-selected limits for one complete analysis."""

    wall_seconds: float | None = None
    rss_bytes: int | None = None
    report_bytes: int | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("wall_seconds", self.wall_seconds),
            ("rss_bytes", self.rss_bytes),
            ("report_bytes", self.report_bytes),
        ):
            if value is not None and value <= 0:
                raise ValueError(f"{label} must be greater than zero")

    def to_dict(self) -> dict[str, Any]:
        """Return report-facing requested limits and enforcement support."""

        return {
            "wallSeconds": self.wall_seconds,
            "rssBytes": self.rss_bytes,
            "reportBytes": self.report_bytes,
            "rssEnforcementSupported": Path("/proc").is_dir(),
        }


@dataclass
class RunBudget:
    """Cooperative resource accounting shared by pipeline and serialization."""

    limits: RunLimits
    started_at: float = field(default_factory=monotonic)
    peak_rss_bytes: int = 0
    crossed: dict[str, Any] | None = None
    sample_interval_seconds: float = DEFAULT_RESOURCE_SAMPLE_INTERVAL_SECONDS
    _lock: threading.Lock = field(
        default_factory=threading.Lock,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if self.sample_interval_seconds <= 0:
            raise ValueError("resource sample interval must be greater than zero")

    def check(self, phase: str) -> None:
        """Raise at a deterministic checkpoint when a supported limit crossed."""

        self.raise_if_crossed()
        if self.limits.wall_seconds is None and self.limits.rss_bytes is None:
            return
        elapsed = max(0.0, monotonic() - self.started_at)
        self._check_value("overall_wall_time", phase, elapsed, self.limits.wall_seconds)
        if self.limits.rss_bytes is None:
            return
        rss = process_tree_rss_bytes(os.getpid())
        if rss is not None:
            with self._lock:
                self.peak_rss_bytes = max(self.peak_rss_bytes, rss)
            self._check_value("process_tree_rss", phase, rss, self.limits.rss_bytes)

    @contextmanager
    def watch(
        self,
        phase: str,
        cancel_event: threading.Event,
    ) -> Iterator[None]:
        """Actively sample a phase and cancel supervised work at first crossing."""

        self.check(phase)
        if self.limits.wall_seconds is None and self.limits.rss_bytes is None:
            yield
            return
        stop_event = threading.Event()
        watcher = threading.Thread(
            target=self._watch_phase,
            args=(phase, cancel_event, stop_event),
            name=f"ladon-resource-{phase}",
            daemon=True,
        )
        watcher.start()

        def stop_watcher() -> None:
            stop_event.set()
            watcher.join(timeout=max(1.0, self.sample_interval_seconds * 2))

        try:
            yield
        except BaseException:
            stop_watcher()
            self.raise_if_crossed()
            raise
        else:
            stop_watcher()
            self.check(phase)
        finally:
            stop_watcher()

    def raise_if_crossed(self) -> None:
        """Raise the first observed crossing with its original phase identity."""

        with self._lock:
            crossing = dict(self.crossed) if self.crossed is not None else None
        if crossing is None:
            return
        raise ResourceLimitExceeded(
            kind=str(crossing["kind"]),
            phase=str(crossing["phase"]),
            observed=crossing["observed"],
            limit=crossing["limit"],
        )

    def check_report_bytes(self, phase: str, observed: int) -> None:
        """Reject an oversized representation before it is published."""

        self._check_value(
            "report_bytes",
            phase,
            observed,
            self.limits.report_bytes,
        )

    def metadata(self) -> dict[str, Any]:
        """Return requested limits, observations, and any controlling crossing."""

        with self._lock:
            peak_rss_bytes = self.peak_rss_bytes
            crossed = dict(self.crossed) if self.crossed else None
        return {
            "requested": self.limits.to_dict(),
            "observed": {
                "observedWallSeconds": max(
                    0.0,
                    monotonic() - self.started_at,
                ),
                "peakRssBytes": peak_rss_bytes or None,
            },
            "crossed": crossed,
        }

    def _watch_phase(
        self,
        phase: str,
        cancel_event: threading.Event,
        stop_event: threading.Event,
    ) -> None:
        """Sample until completion or one configured limit is crossed."""

        while not stop_event.wait(self.sample_interval_seconds):
            try:
                self.check(phase)
            except ResourceLimitExceeded:
                cancel_event.set()
                return

    def _check_value(
        self,
        kind: str,
        phase: str,
        observed: float | int,
        limit: float | int | None,
    ) -> None:
        if limit is None or observed <= limit:
            return
        with self._lock:
            if self.crossed is None:
                self.crossed = {
                    "kind": kind,
                    "phase": phase,
                    "observed": observed,
                    "limit": limit,
                }
            crossing = dict(self.crossed)
        raise ResourceLimitExceeded(
            kind=str(crossing["kind"]),
            phase=str(crossing["phase"]),
            observed=crossing["observed"],
            limit=crossing["limit"],
        )


@dataclass(frozen=True)
class ProgressEvent:
    """One schema-versioned stderr progress event."""

    run_id: str
    phase: str
    kind: str
    status: str
    elapsed_seconds: float
    completed: int | None = None
    total: int | None = None
    cache: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return the stable machine-readable event shape."""

        return {
            "schemaVersion": PROGRESS_SCHEMA_VERSION,
            "runId": self.run_id,
            "phase": self.phase,
            "event": self.kind,
            "status": self.status,
            "elapsedSeconds": round(max(0.0, self.elapsed_seconds), 6),
            "completed": self.completed,
            "total": self.total,
            "cache": dict(sorted(self.cache.items())),
        }


class ProgressReporter:
    """Rate-limited diagnostic writer that never owns report stdout."""

    def __init__(
        self,
        *,
        mode: str,
        run_id: str,
        stream: TextIO | None = None,
        interval_seconds: float = DEFAULT_PROGRESS_INTERVAL_SECONDS,
    ) -> None:
        if mode not in PROGRESS_MODES:
            raise ValueError(f"unsupported progress mode: {mode}")
        if interval_seconds <= 0:
            raise ValueError("progress interval must be greater than zero")
        self.stream = stream or sys.stderr
        self.mode = resolved_progress_mode(mode, self.stream)
        self.run_id = run_id
        self.interval_seconds = interval_seconds
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        """Whether this reporter emits phase events."""

        return self.mode != "off"

    def phase(
        self,
        name: str,
        *,
        completed_interval: int = 100,
    ) -> PhaseProgress:
        """Create one phase lifecycle with periodic bounded updates."""

        return PhaseProgress(
            self,
            name,
            completed_interval=completed_interval,
        )

    def emit(self, event: ProgressEvent) -> None:
        """Write exactly one event to the selected diagnostic stream."""

        if not self.enabled:
            return
        line = (
            json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":"))
            if self.mode == "json"
            else plain_progress_line(event)
        )
        with self._lock:
            self.stream.write(f"{line}\n")
            self.stream.flush()


class PhaseProgress:
    """Lifecycle and heartbeat for one active pipeline phase."""

    def __init__(
        self,
        reporter: ProgressReporter,
        name: str,
        *,
        completed_interval: int,
    ) -> None:
        if completed_interval <= 0:
            raise ValueError("completed progress interval must be greater than zero")
        self.reporter = reporter
        self.name = name
        self.completed_interval = completed_interval
        self.started_at = monotonic()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._state_lock = threading.Lock()
        self._completed: int | None = None
        self._total: int | None = None
        self._cache: dict[str, int] = {}
        self._last_emitted_completed = 0

    def start(self) -> None:
        """Emit phase start and launch the bounded heartbeat when enabled."""

        self.reporter.emit(self._event("start", "running"))
        if not self.reporter.enabled:
            return
        self._thread = threading.Thread(
            target=self._heartbeat,
            name=f"ladon-progress-{self.name}",
            daemon=True,
        )
        self._thread.start()

    def finish(
        self,
        *,
        status: str,
        completed: int | None = None,
        total: int | None = None,
        cache: dict[str, int] | None = None,
    ) -> None:
        """Stop heartbeat and emit one terminal phase event."""

        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=min(1.0, self.reporter.interval_seconds))
        stored_completed, stored_total, stored_cache = self._snapshot()
        self.reporter.emit(
            self._event(
                "finish",
                status,
                completed=(
                    completed if completed is not None else stored_completed
                ),
                total=total if total is not None else stored_total,
                cache=cache if cache is not None else stored_cache,
            )
        )

    def update(
        self,
        *,
        completed: int,
        total: int | None = None,
        cache: dict[str, int] | None = None,
        force: bool = False,
    ) -> None:
        """Publish count progress at bounded unit intervals."""

        if completed < 0 or (total is not None and total < completed):
            raise ValueError("progress counters must describe a valid prefix")
        with self._state_lock:
            self._completed = completed
            self._total = total
            if cache is not None:
                self._cache = dict(cache)
            should_emit = force or (
                completed - self._last_emitted_completed
                >= self.completed_interval
            )
            if should_emit:
                self._last_emitted_completed = completed
                snapshot = (
                    self._completed,
                    self._total,
                    dict(self._cache),
                )
            else:
                snapshot = None
        if snapshot is not None:
            self.reporter.emit(
                self._event(
                    "update",
                    "running",
                    completed=snapshot[0],
                    total=snapshot[1],
                    cache=snapshot[2],
                )
            )

    def _heartbeat(self) -> None:
        while not self._stop.wait(self.reporter.interval_seconds):
            completed, total, cache = self._snapshot(mark_emitted=True)
            self.reporter.emit(
                self._event(
                    "update",
                    "running",
                    completed=completed,
                    total=total,
                    cache=cache,
                )
            )

    def _snapshot(
        self,
        *,
        mark_emitted: bool = False,
    ) -> tuple[int | None, int | None, dict[str, int]]:
        """Read the latest counters without racing a worker update."""

        with self._state_lock:
            if mark_emitted and self._completed is not None:
                self._last_emitted_completed = self._completed
            return self._completed, self._total, dict(self._cache)

    def _event(
        self,
        kind: str,
        status: str,
        *,
        completed: int | None = None,
        total: int | None = None,
        cache: dict[str, int] | None = None,
    ) -> ProgressEvent:
        return ProgressEvent(
            run_id=self.reporter.run_id,
            phase=self.name,
            kind=kind,
            status=status,
            elapsed_seconds=monotonic() - self.started_at,
            completed=completed,
            total=total,
            cache=cache or {},
        )


def resolved_progress_mode(mode: str, stream: TextIO) -> str:
    """Resolve `auto` without adding bytes to redirected automation."""

    if mode != "auto":
        return mode
    is_tty = bool(getattr(stream, "isatty", lambda: False)())
    return "plain" if is_tty else "off"


def plain_progress_line(event: ProgressEvent) -> str:
    """Return one concise human-readable diagnostic event."""

    count = ""
    if event.completed is not None:
        count = f" {event.completed}"
        if event.total is not None:
            count += f"/{event.total}"
    return (
        f"ladon: progress {event.phase} {event.kind} "
        f"{event.status}{count} ({event.elapsed_seconds:.1f}s)"
    )


def process_tree_rss_bytes(root_pid: int) -> int | None:
    """Return Linux process-tree RSS, or `None` when `/proc` is unavailable."""

    proc = Path("/proc")
    if not proc.is_dir():
        return None
    rows = process_rows(proc)
    descendants = descendant_pids(root_pid, rows)
    return sum(rows[pid][1] for pid in descendants if pid in rows)


def process_rows(proc: Path) -> dict[int, tuple[int, int]]:
    """Read bounded parent/RSS facts from numeric Linux proc entries."""

    rows: dict[int, tuple[int, int]] = {}
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        row = process_row(entry)
        if row is not None:
            rows[int(entry.name)] = row
    return rows


def process_row(entry: Path) -> tuple[int, int] | None:
    """Read one `(parent_pid, rss_bytes)` pair, tolerating process races."""

    try:
        status = entry.joinpath("status").read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
        return None
    parent = 0
    rss_kib = 0
    for line in status.splitlines():
        if line.startswith("PPid:"):
            parent = integer_field(line)
        elif line.startswith("VmRSS:"):
            rss_kib = integer_field(line)
    return parent, rss_kib * 1024


def integer_field(line: str) -> int:
    """Parse the first integer following a proc status label."""

    for token in line.split()[1:]:
        if token.isdigit():
            return int(token)
    return 0


def descendant_pids(
    root_pid: int,
    rows: dict[int, tuple[int, int]],
) -> set[int]:
    """Return the root process and every currently observed descendant."""

    selected = {root_pid}
    changed = True
    while changed:
        before = len(selected)
        selected.update(
            pid
            for pid, (parent, _rss) in rows.items()
            if parent in selected
        )
        changed = len(selected) != before
    return selected
