"""Constant-space, request-local observations of supervised process trees."""
from __future__ import annotations

from pathlib import Path

from ladon.progress import descendant_pids, process_rows


class ProcessTreeObserver:
    def __init__(self, proc_root: Path = Path('/proc')):
        self.proc_root = proc_root
        self.samples = 0
        self.unavailable = 0
        self.max_processes = 0
        self.max_lean = 0
        self.largest_lean = 0
        self.unknown_names = 0

    def sample(self, root_pid: int) -> None:
        if not self.proc_root.is_dir():
            self.unavailable += 1
            return
        try:
            rows = process_rows(self.proc_root)
        except OSError:
            self.unavailable += 1
            return
        if root_pid not in rows:
            self.unavailable += 1
            return
        pids = descendant_pids(root_pid, rows)
        lean_rss = [rows[pid][1] for pid in pids if self._is_lean(pid)]
        self.samples += 1
        self.max_processes = max(self.max_processes, len(pids - {root_pid}))
        self.max_lean = max(self.max_lean, len(lean_rss))
        self.largest_lean = max([self.largest_lean, *lean_rss])

    def _is_lean(self, pid: int) -> bool:
        try:
            return (self.proc_root / str(pid) / 'comm').read_text().strip() == 'lean'
        except OSError:
            self.unknown_names += 1
            return False

    def result(self) -> dict:
        available = self.samples > 0
        return {
            'version': 1,
            'status': 'sampled' if available else 'unavailable',
            'samples': self.samples,
            'unavailableSamples': self.unavailable,
            'unidentifiedProcessNames': self.unknown_names,
            'leanMeasurement': 'partial' if self.unknown_names else ('sampled' if available else 'unavailable'),
            'maxDescendantProcesses': self.max_processes if available else None,
            'maxLeanProcesses': self.max_lean if available else None,
            'largestLeanRssBytes': self.largest_lean if available else None,
            'scope': 'sampled supervised process tree; Lean processes identified by kernel comm; transient processes may be missed',
            'memoryMetric': 'RSS per process; shared pages may be counted repeatedly',
        }


def new_observer(enabled: bool) -> ProcessTreeObserver | None:
    return ProcessTreeObserver() if enabled else None


def observed_resources(observer: ProcessTreeObserver | None) -> dict | None:
    return observer.result() if observer is not None else None
