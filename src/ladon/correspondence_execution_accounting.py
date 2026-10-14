"""Bound request-local measurements; timing is never a proof certificate."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from time import monotonic

_CURRENT = ContextVar('ladon_correspondence_accounting', default=None)
_STAGE = ContextVar('ladon_correspondence_stage', default='unclassified')
MAX_PROCESSES = 4096


class ExecutionAccounting:
    def __init__(self):
        self.started = monotonic()
        self.elapsed = None
        self.processes = []
        self.stages = {}

    def record(self, result, bounds):
        if len(self.processes) >= MAX_PROCESSES:
            raise ValueError('correspondence process accounting exceeds bounded population')
        name = _STAGE.get()
        row = {'stage': name, 'command': list(result.command),
               'elapsedSeconds': result.elapsed_seconds, 'returnCode': result.returncode,
               'observedOutputBytes': len((result.stdout + result.stderr).encode()),
               'peakRssBytes': result.peak_rss_bytes, 'timedOut': result.timed_out,
               'outputLimited': result.output_limited, 'memoryLimited': result.memory_limited,
               'bounds': bounds}
        self.processes.append(row)
        stage_row = self.stages.setdefault(name, {'wallSeconds': 0.0, 'processCount': 0})
        stage_row['processCount'] += 1

    def result(self):
        peaks = [r['peakRssBytes'] for r in self.processes if r['peakRssBytes'] is not None]
        return {'profile': 'correspondence-execution-v1',
                'wallSeconds': self.elapsed if self.elapsed is not None else monotonic() - self.started,
                'processCount': len(self.processes), 'processes': list(self.processes),
                'stages': dict(self.stages),
                'observedOutputBytes': sum(r['observedOutputBytes'] for r in self.processes),
                'peakRssBytes': max(peaks, default=None),
                'memoryMeasurementScope': 'supervised process groups; max observed RSS, not cumulative RSS',
                'stageMeasurementScope': 'inclusive wall durations overlap; process counts use innermost labels; do not sum wall stages',
                'concurrency': 'external build/setup overlap is not observed; benchmark operator must disclose it'}


@contextmanager
def execution_accounting():
    if _CURRENT.get() is not None:
        raise ValueError('nested correspondence accounting request')
    owner = ExecutionAccounting()
    token = _CURRENT.set(owner)
    try:
        yield owner
    finally:
        owner.elapsed = monotonic() - owner.started
        _CURRENT.reset(token)


@contextmanager
def stage(name):
    owner = _CURRENT.get()
    started = monotonic()
    token = _STAGE.set(name)
    try:
        yield
    finally:
        _STAGE.reset(token)
        if owner is not None:
            row = owner.stages.setdefault(name, {'wallSeconds': 0.0, 'processCount': 0})
            row['wallSeconds'] += monotonic() - started


def measured_bounded_process(function):
    @wraps(function)
    def run(*args, **kwargs):
        result = function(*args, **kwargs)
        owner = _CURRENT.get()
        if owner is not None:
            owner.record(result, {key: kwargs.get(key) for key in
                         ('timeout_seconds', 'max_output_bytes', 'max_rss_bytes')})
        return result
    return run
