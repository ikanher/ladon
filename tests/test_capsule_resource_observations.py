from __future__ import annotations

import sys

from ladon.process_supervisor import run_bounded_target_process


def test_observer_counts_lean_processes_and_retains_only_bounded_summary(tmp_path, monkeypatch):
    from ladon import process_resource_observations as observations

    rows = {10: (1, 100), 11: (10, 200), 12: (10, 300)}
    for pid, name in ((10, 'lake'), (11, 'lean'), (12, 'lean')):
        (tmp_path / str(pid)).mkdir()
        (tmp_path / str(pid) / 'comm').write_text(name)
    monkeypatch.setattr(observations, 'process_rows', lambda _proc: rows)
    observer = observations.ProcessTreeObserver(proc_root=tmp_path)
    for _ in range(100):
        observer.sample(10)
    result = observer.result()
    assert result['status'] == 'sampled'
    assert result['samples'] == 100
    assert result['maxLeanProcesses'] == 2
    assert result['largestLeanRssBytes'] == 300
    assert result['maxDescendantProcesses'] == 2
    assert 'pids' not in result
    assert 'commands' not in result


def test_observer_explicitly_marks_unavailable_measurement(tmp_path):
    from ladon.process_resource_observations import ProcessTreeObserver

    observer = ProcessTreeObserver(proc_root=tmp_path / 'missing')
    observer.sample(10)
    assert observer.result()['status'] == 'unavailable'
    assert observer.result()['maxLeanProcesses'] is None


def test_supervisor_returns_request_local_observations(tmp_path):
    result = run_bounded_target_process(
        [sys.executable, '-c', 'import time; time.sleep(0.2)'],
        cwd=tmp_path, timeout_seconds=2, max_rss_bytes=128 * 1024**2,
        max_output_bytes=1024, observe_resources=True,
    )
    assert result.succeeded
    assert result.resource_observations['status'] == 'sampled'
    assert result.resource_observations['samples'] > 0
    assert result.resource_observations['maxLeanProcesses'] == 0


def test_observed_timeout_terminates_descendants(tmp_path):
    from pathlib import Path

    code = (
        'import subprocess,sys,time; '
        'child=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); '
        'print(child.pid,flush=True); time.sleep(30)'
    )
    result = run_bounded_target_process(
        [sys.executable, '-c', code], cwd=tmp_path, timeout_seconds=0.4,
        max_rss_bytes=128 * 1024**2, max_output_bytes=1024, observe_resources=True,
    )
    assert result.timed_out
    child = Path('/proc') / result.stdout.strip() / 'stat'
    if child.exists():
        assert child.read_text().split(') ', 1)[1].split()[0] == 'Z'
    assert result.resource_observations['maxDescendantProcesses'] >= 1


def test_observed_memory_exhaustion_preserves_rss_enforcement(tmp_path):
    result = run_bounded_target_process(
        [sys.executable, '-c', 'import time; data=bytearray(64*1024**2); time.sleep(30)'],
        cwd=tmp_path, timeout_seconds=3, max_rss_bytes=32 * 1024**2,
        max_output_bytes=1024, observe_resources=True,
    )
    assert result.memory_limited
    assert result.peak_rss_bytes > 32 * 1024**2
    assert result.resource_observations['status'] == 'sampled'
